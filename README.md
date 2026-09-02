<h1>
  <img src="docs/assets/verdaccio-logo.svg" alt="Verdaccio logo" width="32">
  Verdaccio Kubernetes operator
</h1>

`verdaccio-k8s` is a [Juju](https://juju.is/) charm that deploys and operates a
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
`arm64`; the checked-in local build workflow produces `amd64` artifacts.

## Getting started

The charm and its OCI image are built together from this repository. Follow
[`DEVELOPMENT.md`](DEVELOPMENT.md) to create the local Kubernetes environment, build both
artifacts, and deploy them.

The default registry listens on port `4873` inside the model. Relate the `ingress` endpoint to an
Ingress v2 provider such as `traefik-k8s` to publish it outside the model.

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
