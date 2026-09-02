# Verdaccio workload application

This directory is the source for the OCI image built by `rockcraft.yaml`. It pins
Verdaccio, Node.js telemetry dependencies, and the first-party metrics middleware.
The charm owns the runtime configuration; the image owns only executable code and
plugins.

## Build and test

Install the pinned package manager and use the lockfile:

```bash
corepack enable
pnpm install --frozen-lockfile
pnpm typecheck
pnpm test
pnpm build
```

The Rock uses two parts: `node-runtime` stages the pinned Node.js toolchain from
the dependency-free `node-runtime/package.json`, disables lifecycle scripts, and
primes only `bin/node`; `verdaccio-app` consumes that staged runtime, deletes any
local compiler output, then builds with pnpm, runs type checks and tests, and
prunes development dependencies. Update exact dependency versions deliberately
and regenerate `pnpm-lock.yaml`; never allow the application build to resolve
floating runtime dependencies.

## Observability contract

`instrumentation.ts` starts a Prometheus exporter on `0.0.0.0:9464/metrics` and
registers the global OpenTelemetry meter provider before Verdaccio loads plugins.
Tracing is disabled unless `OTEL_EXPORTER_OTLP_ENDPOINT` is present. When present,
HTTP and Express spans are exported as OTLP/HTTP protobuf. Health and metrics paths
are excluded from tracing to avoid self-generated telemetry volume.

The metrics endpoint uses a separate port so ingress does not expose process metrics.
The charm must publish `*:9464/metrics` on its `prometheus_scrape` relation and must
not open port 9464 through the workload service.

## Adding a plugin or middleware

Keep operator-owned plugins below this directory. Each plugin must:

1. Have its own `package.json`, TypeScript source, strict `tsconfig.json`, and focused
   tests.
2. Export the Verdaccio plugin class as the package default and implement the matching
   `@verdaccio/types` interface.
3. Use a stable package directory name. Verdaccio prefixes unqualified configuration
   keys with `verdaccio-`; for example, the `metrics` key loads
   `/verdaccio/plugins/verdaccio-metrics`.
4. Declare runtime dependencies explicitly. Do not rely on undeclared transitive
   dependencies, network downloads, or install scripts at container startup.
5. Avoid secrets and unbounded values in logs, metrics labels, and span attributes.
   Package names, usernames, URLs, and user-agent strings are not acceptable metrics
   labels.
6. Add the compiled package directory to `rockcraft.yaml` under
   `/verdaccio/plugins`, then add typed charm-owned configuration for it.
7. Test the plugin against the exact pinned Verdaccio version and test the packed Rock
   as Rockcraft's `_daemon_` user before updating the charm resource.

A plugin upgrade is a workload API change. Verify startup, health, configuration
rendering, upgrade behavior, and reconciliation convergence before publishing the new
OCI resource revision.
