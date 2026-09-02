<h1>
  <img src="docs/assets/verdaccio-logo.svg" alt="Verdaccio logo" width="32">
  Verdaccio Kubernetes operator
</h1>

[![Charmhub](https://charmhub.io/verdaccio-k8s/badge.svg)](https://charmhub.io/verdaccio-k8s)

[`verdaccio-k8s`](https://charmhub.io/verdaccio-k8s) is a published
[Juju](https://juju.is/) charm that deploys and operates a
[Verdaccio](https://verdaccio.org/) private npm registry on Kubernetes. The repository also
builds the workload OCI image: Verdaccio 6.10.1 with first-party Prometheus metrics and
OpenTelemetry tracing.

## What it provides

- Persistent package, metadata, and `htpasswd` storage on a Juju filesystem volume.
- An npmjs uplink and package policies that allow public reads and authenticated publishing by
  default.
- Validated Verdaccio configuration for authentication, uplinks, package access, the web UI,
  HTTPS, webhooks, logging, filters, proxies, and other server settings.
- Juju secret-backed uplink tokens, webhook headers, and PKCS#12 passphrases.
- Optional ingress, Loki log forwarding, Prometheus scraping, and Tempo-compatible OTLP/HTTP
  tracing integrations.
- Change-aware Pebble reconciliation and an HTTP readiness check at `/-/ping`.

The charm requires Juju 3.6 or newer on a Kubernetes cloud. Its manifests target `amd64` and
`arm64`; the current Charmhub release and checked-in local build workflow provide `amd64`.

## Deploy

Deploy the published charm from [Charmhub](https://charmhub.io/verdaccio-k8s) on the edge
channel and request a 1 GiB persistent volume:

```bash
juju deploy verdaccio-k8s \
  --channel latest/edge \
  --storage data=1G
juju wait-for application verdaccio-k8s \
  --query='status=="active"' \
  --timeout 10m
juju storage
```

The `data` filesystem is mounted at `/verdaccio/storage` for packages, metadata, and credentials.
The charm remains waiting until this storage is attached.

### Ingress

Deploy Traefik with subdomain routing, wait for it to become active, and integrate it with the
registry:

```bash
juju deploy traefik-k8s \
  --channel latest/stable \
  --trust \
  --config external_hostname=traefik.local \
  --config routing_mode=subdomain
juju wait-for application traefik-k8s \
  --query='status=="active"' \
  --timeout 10m
juju integrate verdaccio-k8s:ingress traefik-k8s:ingress
juju status --relations
```

For a model named `dev`, this publishes Verdaccio at
`http://dev-verdaccio-k8s.traefik.local/`. The hostname must resolve to the Traefik load balancer
from the client network. Use `/-/ping` as a readiness endpoint; a healthy registry returns `{}`.

## Configuration

Inspect the complete option reference, including accepted YAML fields and defaults, with:

```bash
juju config verdaccio-k8s
```

Most structured Verdaccio sections are exposed as YAML fragments without their top-level key.
For example:

```bash
juju config verdaccio-k8s \
  web-config='{title: Team registry, darkMode: true, showFooter: false}' \
  log-config='{type: stdout, format: json, level: info}'
```

### Third-party plugins

`auth-config`, `store-config`, `middlewares-config`, and `filters-config` accept third-party
Verdaccio plugin entries. These options only configure plugins: the charm never downloads or
installs plugin packages. The OCI image supplied through the `verdaccio-image` resource must
already contain every configured plugin under `/verdaccio/plugins`.

To use a third-party plugin, build a custom image containing the plugin and its runtime
dependencies, then deploy or refresh the charm with that image as `verdaccio-image`. See
[`verdaccio-app/README.md`](verdaccio-app/README.md#adding-a-plugin-or-middleware) for the image
layout and build requirements.

Important defaults are:

| Setting | Default |
| --- | --- |
| Listener | HTTP on `0.0.0.0:4873` |
| Storage | `/verdaccio/storage` on the `data` filesystem volume |
| Authentication | `htpasswd` at `/verdaccio/storage/htpasswd` |
| Uplink | `npmjs` at `https://registry.npmjs.org/` |
| Package access | Public read; authenticated publish and unpublish |
| Audit middleware | Enabled |

Credential-bearing values use the native secret options
`uplink-tokens-secret-id`, `webhook-credentials-secret-id`, and
`pfx-passphrase-secret-id`. Create a Juju secret, grant `verdaccio-k8s` access to it, then set the
matching option. The exact secret content schemas are documented in
[`charmcraft.yaml`](charmcraft.yaml).

Invalid public or secret-backed configuration places the unit in a blocked state and identifies
the affected option without including its value.

## Management actions

`manage-user` operates the built-in `htpasswd` backend. Verdaccio does not distinguish an
administrator role: `admin` is a conventional username, while authorization for every account is
defined by `packages-config`.

```bash
juju run verdaccio-k8s/0 manage-user operation=create username=admin
juju run verdaccio-k8s/0 manage-user operation=reset-password username=admin
juju run verdaccio-k8s/0 manage-user operation=list
juju run verdaccio-k8s/0 manage-user operation=remove username=admin
```

Create and reset operations generate a password and return it in the action results. Juju persists
action results in operation history, where the password remains visible to users with model read
access; treat that history as credential-bearing and transfer the password to an appropriate
secret store immediately. User management is rejected when `htpasswd` is not the only configured
authentication plugin.

`manage-token` reports the API and web token modes. Verdaccio does not provide individual token
revocation; global revocation rotates the local-storage signing secret and invalidates every API
and web token.

```bash
juju run verdaccio-k8s/0 manage-token operation=status
juju run verdaccio-k8s/0 manage-token operation=revoke-all confirm=true
```

Global revocation is available only with Verdaccio's local storage backend. Every mutating user
operation and global token revocation temporarily stops the registry while its persistent files
are changed, then restarts it; clients experience a brief service interruption.

## Integrations

| Endpoint | Direction | Purpose |
| --- | --- | --- |
| `ingress` | Requires | Publish the registry through an Ingress v2 provider |
| `metrics-endpoint` | Provides | Publish `*:9464/metrics` for Prometheus scraping |
| `logging` | Requires | Forward workload logs to Loki |
| `tracing` | Requires | Export HTTP spans to an OTLP/HTTP endpoint |

The metrics port is internal and is not exposed by the workload service or ingress.

## Development

See [`DEVELOPMENT.md`](DEVELOPMENT.md) for the environment, test and build commands, local
deployment workflow, and repository layout.
