read_config() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    cat /verdaccio/conf/config.yaml
}

ping_registry() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- "http://127.0.0.1:${1}/-/ping"
}

deploy_ingress() {
  routing_mode="${1}"
  sudo -H -u ubuntu juju deploy \
    --model "${MODEL}" \
    traefik-k8s \
    --channel latest/stable \
    --trust \
    --config external_hostname=traefik.local \
    --config "routing_mode=${routing_mode}"
  sudo -H -u ubuntu env JUJU_MODEL="${MODEL}" juju wait-for \
    application traefik-k8s \
    --query='status=="active"' \
    --timeout 10m
  sudo -H -u ubuntu juju integrate \
    --model "${MODEL}" \
    verdaccio-k8s:ingress \
    traefik-k8s:ingress
}

read_plan() {
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    /charm/bin/pebble plan
}

read_ingress_relation() {
  sudo -H -u ubuntu juju show-unit \
    --model "${MODEL}" \
    traefik-k8s/0 \
    --format yaml
}

fetch_ingress() {
  host="${1}"
  path="${2}"
  sudo -H -u ubuntu juju ssh \
    --model "${MODEL}" \
    --container verdaccio \
    verdaccio-k8s/0 \
    wget -qO- \
    --header="Host:${host}" \
    "http://traefik-k8s-lb.${MODEL}.svc.cluster.local${path}"
}
