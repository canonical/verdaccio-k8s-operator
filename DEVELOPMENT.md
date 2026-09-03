# Development

This repository builds two coupled artifacts: a Verdaccio OCI image from `rockcraft.yaml` and a
Juju charm from `charmcraft.yaml`. The local workflow uses Workshop to provide Docker, Kind,
Juju, Charmcraft, Rockcraft, and `uv` inside an Ubuntu 24.04 LXD container.

## Set up the environment

Install Workshop and LXD on the host:

```bash
sudo snap install --channel=6/stable lxd
sudo snap install --classic workshop
```

Launch the checked-in environment from the repository root:

```bash
workshop launch dev
workshop run dev -- status
```

The full environment definition is in [`.workshop/dev.yaml`](.workshop/dev.yaml). See the
[development environment runbook](docs/tools/dev-environment.md) for lifecycle commands, cluster
reset instructions, implementation constraints, and troubleshooting.

## Test

Run the Python unit suite directly:

```bash
uv run pytest
```

Or run it inside Workshop:

```bash
workshop exec dev -- uv run pytest
```

The suite uses the Ops testing context and covers configuration, secrets, workload convergence,
ingress, storage, and observability. Packed-charm deployment stories live in
[`spread/integration/`](spread/integration/).

First [build and load the artifacts](#build-and-deploy-locally), then run every deployed story or select one:

```bash
workshop run dev -- spread
workshop run dev -- spread local:ubuntu-24.04:spread/integration/default_config
```

The Workshop action runs Spread with the normal `workshop` account. Spread executes every remote
hook as root, so every task must source [`helpers.sh`](spread/integration/helpers.sh); it provides
the single boundary that returns Docker, Juju, and kubectl to the account that owns their state.

Continuous integration runs the same suite: the `Packed-charm integration tests` job in
[`ci.yaml`](.github/workflows/ci.yaml) launches this Workshop on a GitHub-hosted runner with
[`canonical/launch-workshop`](https://github.com/canonical/launch-workshop), then invokes the
`pack-rock`, `load-rock`, `pack-charm`, and `spread` actions. `.workshop/dev.yaml` stays the only
environment definition, so a change that breaks it breaks both paths.

The workload application has its own TypeScript build and test workflow. See
[`verdaccio-app/README.md`](verdaccio-app/README.md).

## Build and deploy locally

Build the workload Rock, load it into Kind, and pack the charm. The checked-in Workshop actions
produce `amd64` artifacts.

```bash
workshop run --uid 0 dev -- pack-rock
workshop run dev -- load-rock
workshop run --uid 0 dev -- pack-charm
```

Deploy the charm with the locally loaded image resource:

```bash
workshop exec dev -- \
  juju deploy ./verdaccio-k8s_amd64.charm --resource verdaccio-image=verdaccio:6.10.1
workshop run dev -- status
```

The build actions run the craft tools in destructive mode inside the matching Ubuntu 24.04
Workshop base. They remove shared craft output directories before packing and restore artifact
ownership to the Workshop user.

## Repository layout

| Path | Contents |
| --- | --- |
| [`src/`](src/) | Charm orchestration, validated configuration, secret handling, and Pebble workload planning |
| [`verdaccio-app/`](verdaccio-app/) | TypeScript instrumentation and metrics middleware included in the OCI image |
| [`tests/unit/`](tests/unit/) | Ops scenario unit tests |
| [`spread/integration/`](spread/integration/) | Deployed integration stories |
| [`docs/code-standards/`](docs/code-standards/) | Normative repository engineering rules |
| [`.workshop/`](.workshop/) | Reproducible local Kubernetes and charm development environment |
