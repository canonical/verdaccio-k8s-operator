# AGENTS.md

Guidance for coding agents working in `verdaccio-k8s-operator`. The authoritative
knowledge lives under `docs/`. Read the relevant file **before** writing code —
do not infer conventions from surrounding code alone.

## Repository

A Kubernetes charm (Juju operator) for Verdaccio, written in Python with the
[Ops](https://github.com/canonical/operator) framework and Pydantic 2, managed
with `uv`.

## Where knowledge lives

`docs/` has three tiers, and they are used differently:

| Path | Tier | Use it for |
| --- | --- | --- |
| `docs/code-standards/` | **Normative.** Rules this repo must satisfy. | Deciding *how* to write something. Violating one of these is a review failure. |
| `docs/tools/*.md` (except below) | **Reference.** Scraped upstream API/example corpora. | Looking up *what* an API is and how it is called. |
| `docs/tools/dev-environment.md` | **Runbook.** First-party, verified. | Building, deploying and testing a charm for real. |

### `docs/code-standards/` — normative rules

Each rule has a stable ID as its heading (`cs:<domain>.<area>.<rule>`), a
one-paragraph rationale, and — in `operator.md` — a **Do** / **Don't** code pair.
Cite the rule ID in commit messages, PR descriptions, and review comments.

- **`docs/code-standards/git.md`** (49 lines) — branch naming, Conventional
  Commits (`type(scope): description`), commit scope selection, PR template,
  squash-merge/protected `main`, `v`-prefixed annotated release tags,
  `.gitignore` ownership (repo-level patterns only; OS/editor ignores go in the
  user's global gitignore). `cs.git.commit.context` requires that a commit made
  through a coding harness record the context, considerations, decisions, and
  spec scope behind it.

- **`docs/code-standards/operator.md`** (813 lines) — the core rules for this
  repo. Read the whole file once; re-read the specific rule when you touch its
  area.

  Configuration & schema boundary:
  - `cs:operator.configuration.schema_boundary` — all untrusted config crosses one Pydantic boundary
  - `cs:operator.configuration.closed_immutable_models` — `ConfigDict(extra="forbid", frozen=True)`
  - `cs:operator.configuration.semantic_types` — constrained fields, `Literal`, model validators
  - `cs:operator.configuration.source_adapters` — adapters produce plain mappings; models never touch the framework
  - `cs:operator.configuration.secrets` — `SecretStr` in memory, revealed only at the output boundary
  - `cs:operator.configuration.output_serialization` — explicit serializers returning `dict[str, str]`
  - `cs:operator.configuration.precedence` — one assembly function, documented precedence
  - `cs:operator.configuration.validation_failure` — `ValidationError` → concise `BlockedStatus`

  Events & reconciliation:
  - `cs:operator.events.holistic_reconciliation` — one reconciler, not delta handlers
  - `cs:operator.events.current_state` — read live state, never trust the event payload
  - `cs:operator.events.reconcile_phases` — read → validate → plan → apply; planning is pure
  - `cs:operator.events.prerequisite_outcomes` — `blocked` vs `waiting` vs no-op
  - `cs:operator.events.defer_sparingly` — prefer returning; `defer()` only for transient conditions
  - `cs:operator.events.idempotent_effects` — converged units mutate nothing
  - `cs:operator.events.content_changes` — digest rotating content, or restart explicitly
  - `cs:operator.events.relation_contracts` — typed, version-aware relation models
  - `cs:operator.events.leadership` — check leadership at the point of mutation, never cache it
  - `cs:operator.events.status_collection` — side-effect free, deterministic priority
  - `cs:operator.events.persisted_state` — only irreducible historical facts
  - `cs:operator.events.action_boundaries` — dedicated synchronous handlers, `event.fail()` on expected failure

  Execution & testing:
  - `cs:operator.execution.argv_commands` — argv, never string-concatenated shell
  - `cs:operator.testing.event_transitions` — assert observable transitions via the Ops testing context
  - `cs:operator.testing.convergence` — every reconciled resource has a run-twice, no-op-second-time test

### `docs/tools/` — upstream reference corpora

Everything here except `dev-environment.md` (see below) is machine-generated:
repeated `### <title>` / `Source: <upstream URL>` / description / code block,
separated by `---`. These files are large — **never read them end to end.** Grep
for the symbol or task, read the surrounding ~40 lines, and follow the `Source:`
URL when you need the real prose docs.

- **`docs/tools/operator.md`** (~15k lines, ~1000 entries) — the Ops framework:
  Pebble client API, charm lifecycle hooks, containers, relations and interface
  testing, secrets, `ops.testing` (Scenario) and the legacy `Harness`, Jubilant
  integration tests, `charmcraft`/`concierge` setup, debugging. Mostly drawn
  from `canonical/operator` `docs/howto`, `docs/reference`, `docs/tutorial`, and
  `docs/explanation`.
- **`docs/tools/pydantic.md`** (~1.6k lines) — Pydantic 2: models, validators,
  serializers, `TypeAdapter`, JSON Schema, V1→V2 migration.
- **`docs/tools/verdaccio.md`** (~2.2k lines, 138 entries) — the workload
  itself, from `verdaccio/verdaccio` (`master` branch, wiki, package READMEs,
  and `docker-examples/v7`). The parts that matter when charming it:
  - **Config file** — `@verdaccio/config` `ConfigBuilder` and
    `getDefaultConfig()` (the most reliable listing of the `config.yaml` keys:
    `storage`, `auth`, `uplinks`, `packages` access rules, `web`, `middlewares`,
    `security`, `i18n`, `log`), plus the `@verdaccio/package-filter` plugin's
    `filters:` block — `allow`/`block` rules by scope, package name, or version
    range, `minAgeDays`/`dateThreshold` cutoffs, and the `replace` strategy.
    Allow rules are evaluated before block rules. `ConfigBuilder.getAsYaml()`
    shows the exact YAML shape the charm must render.
  - **Storage** — `local-storage` (`LocalDatabase`/`LocalFS` constructors) and
    the `memory` storage plugin; Docker local storage volume examples.
  - **Auth** — `htpasswd` plugin config and hashing algorithms, `auth-memory`,
    and the `audit` middleware plugin.
  - **Deployment** — official Docker image, Docker Compose, Helm on Kubernetes,
    and reverse-proxy setups (nginx incl. relative path, Apache, https-portal)
    — the closest upstream analogue to what this charm must reproduce.
  - **Operations** — starting the server, `npm` registry/SSL client config,
    publishing, and debug logging (`DEBUG` env, `--inspect`).

  Note: entries about pnpm builds, changesets, plugin scaffolding, the React UI
  components, and the plugin-verifier CLI describe upstream *development*, not
  runtime configuration — skip them.
- **`docs/tools/uv.md`** — ⚠️ **currently a byte-identical copy of
  `pydantic.md`; it contains no uv documentation.** Do not cite it for uv
  behavior. Until it is regenerated, use `uv help <command>` or
  <https://docs.astral.sh/uv/>.

Example lookup:

```bash
grep -n 'add_layer' docs/tools/operator.md      # find entries
sed -n '3200,3240p' docs/tools/operator.md      # read one entry
```

### `docs/tools/dev-environment.md` — the charm testing environment

The one hand-written file under `docs/tools/`. Unit tests run anywhere; anything
that must actually *deploy* — a packed charm or an integration test — runs in
the Workshop environment it describes, defined by **`.workshop/dev.yaml`**.

Workshop creates an Ubuntu 24.04 LXD system container, mounts the working tree
at `/project`, and composes the `uv`, `docker-ce`, `juju-cli`, and local
`project-charm-dev` SDKs. Docker runs a Kind Kubernetes cluster; the local SDK
installs Kind and Charmcraft and bootstraps a Juju controller.

The runbook explains why `.workshop/charm-dev/kind.yaml` pins Kubernetes 1.35.8
and enables `KubeletInUserNamespace`; preserve both settings unless the complete
Workshop lifecycle is reverified against a replacement node image.

Run it with:

```bash
workshop launch dev
workshop run dev -- status
workshop exec dev -- juju status --color=false
```

Commands run in the mounted working tree, so edits made on the host are what get
built.

Four rules the environment imposes; the runbook explains why each exists:

- Pack with the root action `workshop run --uid 0 dev -- pack-charm`. It uses
  destructive mode because a managed craft build would add another LXD layer.
  The Workshop base must therefore match the charm base (`ubuntu@24.04`).
- The packing action returns `.charm` files to `workshop:workshop`; do not leave
  artifacts owned by root.
- Run Docker, Kind, and Juju **inside** the Workshop. Their state and endpoints
  are local to that environment.
- Use `workshop run dev -- reset-cluster` to replace Kind and bootstrap a fresh
  Juju controller.

## Working rules

1. **Standards beat habit.** When `docs/code-standards/` and a familiar pattern
   disagree, the standard wins. When two standards appear to conflict, say so
   explicitly rather than picking silently.
2. **Reference before invention.** Check `docs/tools/` for the real API
   signature or config key instead of guessing at Ops, Pydantic, or Verdaccio
   behavior.
3. **Cite rule IDs.** Reference `cs:...` IDs in commits, PRs, and review notes
   so decisions stay traceable.
4. **Never auto-commit.** Make the edits and stop. Run `git commit` or
   `git push` only when the user explicitly asks in that message.
5. **Verify.** Prove behavior changes with the Ops testing context — including
   the run-twice convergence assertion required by
   `cs:operator.testing.convergence`. Prove deployment changes by packing and
   deploying in the environment from `docs/tools/dev-environment.md` and reading
   the resulting `juju status`.
