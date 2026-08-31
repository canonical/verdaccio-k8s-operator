#!/usr/bin/env bash
# charm-dev-env.sh — create and manage the LXD charm development environment.
#
# Runs ON the LXD host (see docs/tools/dev-environment.md). Creates one nested
# container holding Docker, a kind cluster, a bootstrapped Juju controller,
# charmcraft and rockcraft, with the project directory bind-mounted into it.
#
# Usage: charm-dev-env.sh <command> [args]
set -euo pipefail

NAME="${CHARM_DEV_NAME:-charm-dev}"
IMAGE="${CHARM_DEV_IMAGE:-ubuntu:24.04}"
KIND_VERSION="${KIND_VERSION:-v0.33.0}"
JUJU_CHANNEL="${JUJU_CHANNEL:-3/stable}"
CPUS="${CHARM_DEV_CPUS:-6}"
MEMORY="${CHARM_DEV_MEMORY:-12GiB}"
DISK="${CHARM_DEV_DISK:-60GiB}"
# kind's published API port. Fixed so the endpoint is deterministic.
API_PORT="${CHARM_DEV_API_PORT:-6443}"
# The project tree, bind-mounted into the container. Defaults to the repository
# this script lives in.
PROJECT_DIR="${CHARM_DEV_PROJECT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

DOCKER_POOL=dockerfs
DOCKER_VOLUME="${NAME}-docker"
CLUSTER="$NAME"
CONTROLLER="$NAME"
WORKDIR=/home/ubuntu/work
PROJECT_MOUNT="$WORKDIR/$(basename "$PROJECT_DIR")"

log() { printf '\033[1;34m::\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# Run as root inside the container. stdin is closed: `lxc exec` forwards it into
# the container, which would otherwise swallow a caller's pipeline.
inc() { lxc exec "$NAME" -- bash -euo pipefail -c "$1" </dev/null; }
# Run as the unprivileged ubuntu user inside the container. `su -` passes the
# script as a single argument, so embedded newlines survive intact; `sudo -i`
# re-quotes it and mangles heredocs.
asdev() { lxc exec "$NAME" -- su - ubuntu -c "set -euo pipefail; $1" </dev/null; }

exists() { lxc info "$NAME" >/dev/null 2>&1; }

require_host() {
  command -v lxc >/dev/null || die "lxc not found; this command runs on the LXD host"
  lxc info >/dev/null 2>&1 || die "cannot reach the LXD daemon (is the user in the 'lxd' group?)"
}

check_sysctls() {
  # kind runs one kubelet + control plane per node container; the defaults on a
  # desktop kernel are usually fine, but a low value fails in confusing ways.
  local watches instances
  watches=$(sysctl -n fs.inotify.max_user_watches)
  instances=$(sysctl -n fs.inotify.max_user_instances)
  ((watches >= 524288)) || log "WARNING: fs.inotify.max_user_watches=$watches (<524288); kind may fail"
  ((instances >= 512)) || log "WARNING: fs.inotify.max_user_instances=$instances (<512); kind may fail"
}

cmd_create() {
  require_host
  check_sysctls

  if ! lxc profile show "$NAME" >/dev/null 2>&1; then
    log "creating LXD profile $NAME"
    lxc profile create "$NAME" >/dev/null
  fi
  # security.nesting is the whole point: Docker (and therefore kind) runs inside
  # the container. Do NOT add `raw.lxc: lxc.apparmor.profile=unconfined` — it
  # breaks snapd, which needs LXD's nested AppArmor namespace to load profiles.
  lxc profile edit "$NAME" <<EOF
name: $NAME
description: Nested LXD container for kind + juju + charmcraft/rockcraft
config:
  linux.kernel_modules: overlay,br_netfilter,ip_tables,ip6_tables,nf_nat
  security.nesting: "true"
devices: {}
EOF

  # Docker's overlayfs driver refuses to run on a ZFS-backed rootfs and silently
  # degrades to vfs. Give /var/lib/docker a dir-pool volume (host ext4) instead.
  lxc storage show "$DOCKER_POOL" >/dev/null 2>&1 || {
    log "creating storage pool $DOCKER_POOL (dir)"
    lxc storage create "$DOCKER_POOL" dir >/dev/null
  }
  lxc storage volume show "$DOCKER_POOL" "$DOCKER_VOLUME" >/dev/null 2>&1 || {
    log "creating storage volume $DOCKER_VOLUME"
    lxc storage volume create "$DOCKER_POOL" "$DOCKER_VOLUME" >/dev/null
  }

  if exists; then
    log "container $NAME already exists"
    lxc start "$NAME" >/dev/null 2>&1 || true
  else
    log "launching $NAME from $IMAGE"
    lxc launch "$IMAGE" "$NAME" -p default -p "$NAME" \
      -c "limits.cpu=$CPUS" -c "limits.memory=$MEMORY" -d "root,size=$DISK" >/dev/null
    lxc config device add "$NAME" docker disk \
      pool="$DOCKER_POOL" source="$DOCKER_VOLUME" path=/var/lib/docker >/dev/null
    inc 'cloud-init status --wait >/dev/null 2>&1 || true'
  fi

  log "installing docker"
  inc '
    if ! command -v docker >/dev/null; then
      export DEBIAN_FRONTEND=noninteractive
      apt-get update -qq
      apt-get install -y -qq docker.io >/dev/null
    fi
    systemctl enable --now docker >/dev/null
    id -nG ubuntu | grep -qw docker || usermod -aG docker ubuntu
    test "$(docker info --format "{{.Driver}}")" != vfs ||
      { echo "docker fell back to the vfs storage driver"; exit 1; }
  '

  log "installing kind $KIND_VERSION"
  inc "
    if [ \"\$(kind version 2>/dev/null | awk '{print \$2}')\" != $KIND_VERSION ]; then
      curl -fsSL -o /tmp/kind https://kind.sigs.k8s.io/dl/$KIND_VERSION/kind-linux-amd64
      install -m0755 /tmp/kind /usr/local/bin/kind && rm -f /tmp/kind
    fi
  "

  log "installing juju, kubectl, charmcraft, rockcraft"
  inc "
    snap list juju >/dev/null 2>&1       || snap install juju --channel=$JUJU_CHANNEL
    snap list kubectl >/dev/null 2>&1    || snap install kubectl --classic
    snap list charmcraft >/dev/null 2>&1 || snap install charmcraft --classic
    snap list rockcraft >/dev/null 2>&1  || snap install rockcraft --classic
    mkdir -p $WORKDIR && chown ubuntu:ubuntu $WORKDIR
  "

  mount_project

  create_cluster
  bootstrap_juju
  cmd_status
}

# Bind-mount the project into the container. `shift=true` idmaps the mount so
# host uid/gid appear unchanged inside: the container's `ubuntu` user (1000) and
# the host user (1000) can both read and write the same files.
mount_project() {
  [ -d "$PROJECT_DIR" ] || die "project directory not found: $PROJECT_DIR"
  local current
  current=$(lxc config device get "$NAME" project source 2>/dev/null || true)
  if [ "$current" = "$PROJECT_DIR" ]; then
    log "project already mounted at $PROJECT_MOUNT"
    return
  fi
  [ -z "$current" ] || lxc config device remove "$NAME" project >/dev/null
  log "mounting $PROJECT_DIR at $PROJECT_MOUNT"
  lxc config device add "$NAME" project disk \
    source="$PROJECT_DIR" path="$PROJECT_MOUNT" shift=true >/dev/null
}

# The attached device is the source of truth for where the project lives inside
# the container: `mount` may have repointed it since this script last ran.
current_mount() {
  lxc config device get "$NAME" project path 2>/dev/null || true
}

create_cluster() {
  if asdev "kind get clusters 2>/dev/null | grep -qx $CLUSTER"; then
    log "kind cluster $CLUSTER already exists"
  else
    log "creating kind cluster $CLUSTER"
    # Written on the host and piped in: a heredoc that has to survive `lxc exec`
    # plus `su -c` quoting is a trap. The API port is pinned so the kubeconfig
    # endpoint (and juju's stored port-forward proxy config) stays predictable.
    printf '%s\n' \
      'kind: Cluster' \
      'apiVersion: kind.x-k8s.io/v1alpha4' \
      'networking:' \
      '  apiServerAddress: "127.0.0.1"' \
      "  apiServerPort: $API_PORT" |
      lxc exec "$NAME" -- su - ubuntu -c 'mkdir -p ~/.kube && cat > /tmp/kind.yaml'
    asdev "kind create cluster --name $CLUSTER --config /tmp/kind.yaml --wait 180s"
  fi
  asdev "kind export kubeconfig --name $CLUSTER && kubectl wait --for=condition=Ready node --all --timeout=180s"
}

bootstrap_juju() {
  # The juju snap is strictly confined and cannot create ~/.local itself.
  asdev "mkdir -p ~/.local/share/juju"
  # A registration is only useful if the controller still answers. Recreating the
  # cluster mints a new Kubernetes CA, which leaves the stored registration
  # pointing at a controller whose certificate no longer verifies.
  if asdev "juju controllers --format=json 2>/dev/null | grep -q '\"$CONTROLLER\"'"; then
    if asdev "timeout 60 juju status -m $CONTROLLER:controller >/dev/null 2>&1"; then
      log "juju controller $CONTROLLER already bootstrapped"
      return
    fi
    log "dropping stale registration for controller $CONTROLLER"
    asdev "juju unregister $CONTROLLER --no-prompt >/dev/null 2>&1 || true"
  fi
  log "registering kind as a juju k8s cloud"
  asdev "juju remove-k8s $CLUSTER --client >/dev/null 2>&1 || true; juju add-k8s $CLUSTER --client"
  log "bootstrapping juju controller $CONTROLLER (a few minutes)"
  asdev "juju bootstrap $CLUSTER $CONTROLLER"
  asdev "juju add-model dev 2>/dev/null || true"
}

cmd_reset_cluster() {
  require_host
  exists || die "container $NAME does not exist"
  log "destroying juju controller and kind cluster"
  asdev "juju kill-controller $CONTROLLER --no-prompt -t 60s >/dev/null 2>&1 || true"
  asdev "juju unregister $CONTROLLER --no-prompt >/dev/null 2>&1 || true"
  asdev "kind delete cluster --name $CLUSTER"
  create_cluster
  bootstrap_juju
  cmd_status
}

cmd_status() {
  require_host
  exists || { echo "container $NAME: absent"; return; }
  lxc list "^$NAME\$" -c ns4
  echo "project: $(lxc config device get "$NAME" project source 2>/dev/null || echo '<none>') -> $(current_mount)"
  inc 'docker info --format "docker:  {{.ServerVersion}} driver={{.Driver}}"' || true
  asdev "
    echo \"kind:    \$(kind version | awk '{print \$2}') clusters=\$(kind get clusters 2>/dev/null | tr '\n' ' ')\"
    echo \"k8s:     \$(kubectl get nodes --no-headers 2>/dev/null | awk '{print \$1, \$2, \$5}')\"
    echo \"juju:    \$(juju version)\"
    juju controllers 2>/dev/null | tail -n +1 || true
  " || true
}

cmd_shell() {
  require_host
  exists || die "container $NAME does not exist"
  local cwd; cwd=$(current_mount)
  lxc exec "$NAME" --cwd "${cwd:-$WORKDIR}" -- sudo -iu ubuntu
}

# Commands run in the mounted project directory: this is the working tree, live,
# with no copy step between the host and the container.
cmd_exec() {
  require_host
  exists || die "container $NAME does not exist"
  asdev "cd '$(current_mount)' 2>/dev/null || cd $WORKDIR; $*"
}

cmd_mount() {
  require_host
  exists || die "container $NAME does not exist"
  [ $# -eq 0 ] || PROJECT_DIR="$(cd "$1" && pwd)"
  PROJECT_MOUNT="$WORKDIR/$(basename "$PROJECT_DIR")"
  mount_project
}

cmd_start() { require_host; lxc start "$NAME"; }
cmd_stop() { require_host; lxc stop "$NAME"; }

cmd_destroy() {
  require_host
  log "deleting container $NAME"
  lxc delete -f "$NAME" >/dev/null 2>&1 || true
  lxc profile delete "$NAME" >/dev/null 2>&1 || true
  lxc storage volume delete "$DOCKER_POOL" "$DOCKER_VOLUME" >/dev/null 2>&1 || true
  log "done (storage pool $DOCKER_POOL kept; it may be shared)"
}

usage() {
  cat >&2 <<EOF
usage: ${0##*/} <command>

  create          create/repair the container, kind cluster and juju controller
  destroy         delete the container, profile and docker volume
  start | stop    start or stop the container
  status          show container, docker, kind, kubernetes and juju state
  shell           interactive shell as the 'ubuntu' user
  exec <cmd...>   run a command as 'ubuntu' in the mounted project directory
  mount [dir]     bind-mount a project directory (default: this repository)
  reset-cluster   recreate the kind cluster and juju controller in place

environment: CHARM_DEV_NAME CHARM_DEV_IMAGE KIND_VERSION JUJU_CHANNEL
             CHARM_DEV_CPUS CHARM_DEV_MEMORY CHARM_DEV_DISK CHARM_DEV_API_PORT
             CHARM_DEV_PROJECT
EOF
  exit 2
}

case "${1:-}" in
  create) shift; cmd_create "$@" ;;
  destroy) shift; cmd_destroy "$@" ;;
  start) shift; cmd_start "$@" ;;
  stop) shift; cmd_stop "$@" ;;
  status) shift; cmd_status "$@" ;;
  shell) shift; cmd_shell "$@" ;;
  exec) shift; [ $# -gt 0 ] || usage; cmd_exec "$@" ;;
  mount) shift; cmd_mount "$@" ;;
  reset-cluster) shift; cmd_reset_cluster "$@" ;;
  *) usage ;;
esac
