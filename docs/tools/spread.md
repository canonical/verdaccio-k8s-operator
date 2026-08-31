# Spread

> Spread is a Go command-line tool for distributing full-system integration tests and other shell-driven tasks across local containers, local virtual machines, and remote infrastructure. It expands project configuration into a matrix of backends, systems, suites, tasks, variants, and samples, then schedules those jobs across reusable workers connected through SSH.

Spread is not a CI service or test framework. It is a task orchestrator that describes what to run, where to run it, and which setup, cleanup, and debugging actions surround each task.

- Repository: https://github.com/canonical/spread
- Primary documentation: https://github.com/canonical/spread/blob/master/README.md
- License: GNU GPL v3 or later
- Go module: `github.com/canonical/spread`
- Main CLI: `cmd/spread`
- Main package: `spread`
- Default branch: `master`

## Quick start

Install the CLI:

```shell
go install github.com/canonical/spread/cmd/spread@latest
```

A minimal project needs a `spread.yaml` or `.spread.yaml` file and at least one suite directory containing a task.

```yaml
# spread.yaml
project: hello-world

backends:
    lxd:
        systems:
            - ubuntu-24.04

path: /root/hello-world

suites:
    examples/:
        summary: Simple examples
```

```yaml
# examples/hello/task.yaml
summary: Greet the planet

execute: |
    echo "Hello world!"
```

Run all selected jobs from anywhere inside the project tree:

```shell
spread
```

Inspect the expanded job matrix without running it:

```shell
spread -list
```

Run a narrower selection:

```shell
spread examples/hello
spread lxd:ubuntu-24.04:examples/hello
```

The local LXD backend requires a working `lxc` installation and an initialized LXD environment.

## Core model

Spread turns configuration into a cascading job matrix.

### Project

A `Project` is loaded from the nearest `spread.yaml` or `.spread.yaml`, searching from the current directory upward. It defines:

- the project name;
- available backends and systems;
- suites;
- the absolute remote project path;
- project-wide environment and lifecycle scripts;
- upload inclusion, exclusion, rename, reroot, and repack rules;
- warning and kill timeouts.

Implementation:

- [`Project` and project loading](https://github.com/canonical/spread/blob/master/spread/project.go)
- [`Load`](https://github.com/canonical/spread/blob/master/spread/project.go#L496)
- [`readProject`](https://github.com/canonical/spread/blob/master/spread/project.go#L711)

### Backend

A backend defines how systems are allocated and discarded. A backend has a configured name and a provider `type`. When `type` is omitted, the backend name is used as its type.

Supported types are:

- `lxd`
- `qemu`
- `google`
- `openstack`
- `linode`
- `adhoc`
- `humbox`

Backend-wide settings include systems, credentials, location, plan, storage, environment, variants, lifecycle scripts, timeouts, priority, and manual selection. Some fields are provider-specific.

Implementation:

- [`Backend`](https://github.com/canonical/spread/blob/master/spread/project.go#L50)
- [`Provider` and `Server` interfaces](https://github.com/canonical/spread/blob/master/spread/provider.go#L14)
- [Provider construction in `Start`](https://github.com/canonical/spread/blob/master/spread/runner.go#L65-L95)

### System

A system identifies the operating-system image and worker configuration used by a backend. Systems may use concise syntax:

```yaml
systems:
    - ubuntu-24.04
```

Or extended syntax:

```yaml
systems:
    - ubuntu-24.04:
        image: ubuntu:24.04
        workers: 2
        username: ubuntu
        password: ubuntu
        storage: 20G
        plan: provider-specific-plan
```

Supported system fields include:

- `image`
- `kernel`
- `username`
- `password`
- `workers`
- `storage`
- `networks`
- `groups`
- `secure-boot`
- `bios`
- `cpu-family`
- `plan`
- `environment`
- `variants`
- `priority`
- `manual`

A missing worker count defaults to one. Negative worker counts are rejected.

Implementation: [`System`](https://github.com/canonical/spread/blob/master/spread/project.go#L118).

### Suite

A suite groups related tasks and corresponds to a directory. Suite names in project configuration must end in `/`.

```yaml
suites:
    integration/:
        summary: Full-system integration tests
```

Spread scans the suite directory. Each direct child directory containing `task.yaml` becomes a task.

Suites can define:

- `summary`
- backend, system, and variant filters
- environment
- `prepare`, `restore`, and `debug`
- `prepare-each`, `restore-each`, and `debug-each`
- warning and kill timeouts
- priority
- manual selection

Implementation: [`Suite`](https://github.com/canonical/spread/blob/master/spread/project.go#L319).

### Task

A task is a directory containing `task.yaml`. Its primary operation is the `execute` shell script.

```yaml
summary: Exercise the service

prepare: |
    install-test-dependencies

execute: |
    run-integration-test

debug: |
    journalctl --no-pager -n 100

restore: |
    remove-test-state
```

Task fields include:

- `summary` and `details`
- backend, system, and variant filters
- environment
- `samples`
- `prepare`, `execute`, `debug`, and `restore`
- artifacts
- warning and kill timeouts
- priority
- manual selection

Task names are formed from the suite path and task directory, for example `integration/api`.

Implementation: [`Task`](https://github.com/canonical/spread/blob/master/spread/project.go#L347).

### Variant

Variants duplicate a task with selected environment values and filters, avoiding copied task definitions.

A suffix after `/` associates an environment entry with one or more variants:

```yaml
environment:
    DATABASE/postgres: postgres
    DATABASE/mysql: mysql
    MODE/debug,trace: verbose
```

Variant definitions cascade across project, backend, system, suite, and task configuration. Lists support:

- plain entries to replace the inherited selection;
- `+name` to add matching values;
- `-name` to remove matching values;
- shell-style wildcard matching.

Implementation:

- [`Environment.Variant`](https://github.com/canonical/spread/blob/master/spread/project.go#L200)
- [`SplitVariants`](https://github.com/canonical/spread/blob/master/spread/project.go#L482)
- [`evalstr`](https://github.com/canonical/spread/blob/master/spread/project.go#L1222)

### Sample

The task-level `samples` field expands one task into numbered jobs. Sample suffixes use `#N`, and filters may select one sample or a range:

```shell
spread suite/task#2
spread suite/task#2..5
```

For a sampled task, the scheduler keeps selecting the lowest pending sample for the same backend, system, and task before moving elsewhere.

Implementation:

- [Sample expansion](https://github.com/canonical/spread/blob/master/spread/project.go#L940-L958)
- [`minSampleForTask`](https://github.com/canonical/spread/blob/master/spread/runner.go#L726)

### Job

A `Job` is the fully expanded unit of work containing exactly one project, backend, system, suite, task, variant, and sample.

Names have these forms:

```text
backend:system:suite/task
backend:system:suite/task:variant
backend:system:suite/task:variant#sample
```

Each job receives a merged environment, effective priority, lifecycle scripts, and inherited timeouts.

Implementation:

- [`Job`](https://github.com/canonical/spread/blob/master/spread/project.go#L378)
- [`Project.Jobs`](https://github.com/canonical/spread/blob/master/spread/project.go#L863)

### Worker

A worker is a backend/system execution loop backed by one allocated or reused server. `system.workers` controls maximum parallelism for that system, capped by the number of matching jobs.

Workers pull jobs from a shared pending queue. They prefer:

1. jobs with the highest priority;
2. another task in the currently active suite, reducing suite setup and teardown;
3. suites with fewer active workers;
4. a pseudo-random order generated from the run seed.

Implementation:

- [Worker count and startup](https://github.com/canonical/spread/blob/master/spread/runner.go#L192-L235)
- [`Runner.worker`](https://github.com/canonical/spread/blob/master/spread/runner.go#L532)
- [`Runner.job`](https://github.com/canonical/spread/blob/master/spread/runner.go#L678)

## Configuration cascade

Environment and selection configuration cascades in this order:

```text
Project -> Backend -> System -> Suite -> Task
```

Later levels override earlier environment variables. References to previously defined variables are evaluated in order.

Host-side shell substitution uses:

```yaml
key: "$(HOST: echo "$API_KEY")"
```

Regular shell substitutions that remain in environment values are evaluated when the remote shell processes the exported value.

Spread injects these variables into every job:

- `SPREAD_JOB`
- `SPREAD_PROJECT`
- `SPREAD_PATH`
- `SPREAD_BACKEND`
- `SPREAD_SYSTEM`
- `SPREAD_SUITE`
- `SPREAD_TASK`
- `SPREAD_VARIANT`
- `SPREAD_SAMPLE`

The evaluated project environment also receives `SPREAD_BACKENDS`, containing the selected backend names.

Provider-specific AdHoc allocation scripts receive:

- `SPREAD_BACKEND`
- `SPREAD_SYSTEM`
- `SPREAD_SYSTEM_USERNAME`
- `SPREAD_SYSTEM_PASSWORD`
- `SPREAD_SYSTEM_ADDRESS`
- `SPREAD_PASSWORD` when the system does not provide its own password

Implementation:

- [Environment evaluation and job variables](https://github.com/canonical/spread/blob/master/spread/project.go#L863-L1068)
- [Host command evaluation](https://github.com/canonical/spread/blob/master/spread/project.go#L1114-L1196)
- [AdHoc allocation environment](https://github.com/canonical/spread/blob/master/spread/adhoc.go#L105-L123)

## Selection, manual entries, variants, and priority

Positional CLI arguments filter expanded job names. `...` acts as a wildcard within a name component, and colon-separated expressions may match multiple ordered components.

Examples:

```shell
spread lxd
spread ubuntu-24.04
spread tests/
spread /task-name
spread lxd:tests/
spread ubuntu-...:tests/task
spread -list tests/
```

The `manual: true` setting is available on backends, systems, suites, and tasks. A manual entry runs only when selection arguments explicitly target it and no matching non-manual entry at the same level takes precedence.

`priority` is inherited from the nearest explicitly configured task, suite, system, or backend value. Larger values run first; zero is the default and negative values are valid.

Implementation:

- [`NewFilter`](https://github.com/canonical/spread/blob/master/spread/project.go#L794)
- [Manual filtering](https://github.com/canonical/spread/blob/master/spread/project.go#L1004-L1022)
- [Priority scheduling](https://github.com/canonical/spread/blob/master/spread/runner.go#L685-L721)
- [Manual-selection integration fixture](https://github.com/canonical/spread/blob/master/tests/manual/spread.yaml)

## Execution lifecycle

The main CLI loads the project, expands jobs, constructs a `Runner`, starts workers, and waits for completion.

High-level flow:

1. Load and validate the nearest project configuration.
2. Expand the backend/system/suite/task/variant/sample matrix.
3. Package project content locally.
4. Create one provider for every configured backend.
5. Open and lock the reuse state file.
6. Determine worker counts.
7. Allocate or reconnect to systems.
8. establish SSH access;
9. upload project content unless reusable content is retained;
10. execute project, backend, suite, and task lifecycle scripts;
11. retrieve requested artifacts;
12. restore state;
13. retain or discard servers;
14. report successful, aborted, and failed operations.

Entry points:

- [`cmd/spread/main.go`](https://github.com/canonical/spread/blob/master/cmd/spread/main.go)
- [`spread.Start`](https://github.com/canonical/spread/blob/master/spread/runner.go#L65)
- [`Runner.loop`](https://github.com/canonical/spread/blob/master/spread/runner.go#L144)

### Lifecycle ordering

Project and backend setup happen once per worker. Suite setup is retained while that worker continues processing jobs in the same suite.

Per-task scripts are composed as follows:

```text
prepare:
    project prepare-each
    backend prepare-each
    suite prepare-each
    task prepare

execute:
    task execute

restore:
    task restore
    suite restore-each
    backend restore-each
    project restore-each
```

The corresponding project, backend, and suite `prepare` and `restore` scripts surround their respective scopes.

Debug scripts are combined in this order after a failure:

```text
task debug
suite debug-each
backend debug-each
project debug-each
```

Restore scripts run after prepare or execute failures unless the run uses `-abend`. A task restore failure marks the worker's project state as bad and prevents further work on that server. Suite restore failure similarly stops safe continuation.

Implementation:

- [`Job.Prepare`, `Job.Restore`, and `Job.Debug`](https://github.com/canonical/spread/blob/master/spread/project.go#L411-L421)
- [Worker lifecycle handling](https://github.com/canonical/spread/blob/master/spread/runner.go#L532-L676)

## Remote shell execution

Spread connects to allocated systems through SSH. It normally executes scripts through `/bin/bash` with:

```shell
set -eu
```

Task scripts execute as root. If configured credentials use a non-root account, that account must support passwordless `sudo`; Spread invokes commands through `sudo -i`.

Before tracing begins, Spread exports the job environment without tracing it, reducing accidental disclosure of secrets. It then enables `set -x` for normal traced task execution.

The remote execution environment also sets:

- `DEBIAN_FRONTEND=noninteractive`
- `DEBIAN_PRIORITY=critical`
- a standard system `PATH` including `/snap/bin`

The SSH client currently uses password authentication and does not validate host keys.

Implementation:

- [`Dial`](https://github.com/canonical/spread/blob/master/spread/client.go#L38)
- [Remote script construction](https://github.com/canonical/spread/blob/master/spread/client.go#L323-L491)
- [`Client.sudo`](https://github.com/canonical/spread/blob/master/spread/client.go#L494)

## Script helper functions

Remote task scripts can use:

- `REBOOT [key]`: request a system reboot and rerun the same script;
- `MATCH <regexp>`: require standard input to match an extended regular expression;
- `NOMATCH <regexp>`: require standard input not to match;
- `ERROR [message]`: fail with a concise error instead of the normal trace.

Local AdHoc and repack scripts additionally support:

- `ADDRESS <ssh-address>`: report an allocated server address;
- `FATAL [message]`: report a non-retryable allocation failure;
- `ERROR [message]`: report a retryable failure.

### Reboots

When `REBOOT` is called, Spread:

1. recognizes the special exit status and marker;
2. reads `/proc/sys/kernel/random/boot_id`;
3. requests a reboot;
4. reconnects until the boot ID changes;
5. reruns the complete script.

`SPREAD_REBOOT` starts at `0` and normally increments after each reboot. A custom `REBOOT value` argument becomes the next value. More than ten reboot requests fail the job.

Implementation: [Reboot handling in `Client.run`](https://github.com/canonical/spread/blob/master/spread/client.go#L262-L304).

## Timeouts and failures

The default warning timeout is five minutes. The default kill timeout is fifteen minutes.

Configure them at project, backend, suite, or task level:

```yaml
warn-timeout: 2m
kill-timeout: 30m
```

The nearest configured value applies to a script's context. `-1` disables a timeout by mapping it to the implementation's maximum duration.

While a command runs:

- each warning interval reports new output, unchanged output, or still-empty output;
- reaching the kill timeout signals the remote session with `SIGKILL`;
- local helper scripts are killed directly.

Server allocation is retried up to three times at the runner level. An individual allocation attempt has a five-minute deadline. `FatalError` prevents retries.

Final statistics distinguish:

- successful tasks;
- aborted tasks;
- failed task execution;
- task prepare and restore errors;
- suite prepare and restore errors;
- backend prepare and restore errors;
- project prepare and restore errors.

Any aborted task or lifecycle error makes the run unsuccessful.

Implementation:

- [Default timeouts](https://github.com/canonical/spread/blob/master/spread/client.go#L668-L672)
- [Remote command timeout loop](https://github.com/canonical/spread/blob/master/spread/client.go#L674-L733)
- [Allocation retries](https://github.com/canonical/spread/blob/master/spread/runner.go#L869-L966)
- [`FatalError`](https://github.com/canonical/spread/blob/master/spread/provider.go#L31)
- [Run statistics](https://github.com/canonical/spread/blob/master/spread/runner.go#L1029-L1102)

## Project transfer, reroot, repack, and artifacts

### Project content

Spread creates a tar archive of project content before workers begin. By default, it includes top-level project entries and excludes reuse state.

Configuration fields:

- `path`: required absolute destination on each worker; `/` is rejected;
- `reroot`: changes the local directory treated as the project root;
- `include`: entries included in the tar archive;
- `exclude`: tar exclusion patterns;
- `rename`: GNU tar transform expressions;
- `repack`: a local transformation script.

When `repack` is absent, Spread creates a gzipped tar directly. When present, uncompressed tar data is passed to the script on file descriptor 3, and the script must write transformed tar data to file descriptor 4; Spread then gzip-compresses the result.

Implementation:

- [`Runner.prepareContent`](https://github.com/canonical/spread/blob/master/spread/runner.go#L252-L423)
- [Project transfer through `SendTar`](https://github.com/canonical/spread/blob/master/spread/client.go#L612-L636)
- [Repack integration fixture](https://github.com/canonical/spread/tree/master/tests/repack)

### Artifacts

A task registers relative files or directories:

```yaml
artifacts:
    - test-results.xml
    - logs/
```

Fetch them with:

```shell
spread -artifacts=./artifacts suite/task
```

Artifacts are placed under a directory named after the complete job:

```text
artifacts/backend:system:suite/task:variant/
```

Retrieval occurs after task execution, whether it succeeds or fails, provided the run has not abended. Missing paths are tolerated by the remote tar command. Artifact paths must be clean, relative paths that do not escape the task directory.

Implementation:

- [Artifact path validation](https://github.com/canonical/spread/blob/master/spread/project.go#L697-L701)
- [`Runner.fetchArtifacts`](https://github.com/canonical/spread/blob/master/spread/runner.go#L819-L849)
- [Artifact integration fixture](https://github.com/canonical/spread/tree/master/tests/artifacts)

## Reuse, resend, restore, discard, and recovery

Use `-reuse` to retain servers and their uploaded project content between runs:

```shell
spread -reuse suite/task
```

Persistent reuse state is stored in:

```text
.spread-reuse.yaml
```

Without `-reuse`, process-specific state is stored in:

```text
.spread-reuse.<pid>.yaml
```

The reuse file stores backend, system, SSH address, credentials, and provider-specific data. It is locked with `flock`. Updates use temporary files and rename steps so that a later process can recover from an interrupted write.

Important modes:

- `-reuse`: keep and reconnect to workers;
- `-resend`: remove and resend project content on reused workers;
- `-discard`: discard tracked reused workers without running jobs;
- `-reuse-pid=N`: recover resources tracked by a crashed process;
- `-restore`: skip prepare and execute, running restoration logic only.

After an interrupted non-reuse run, Spread prints a recovery command:

```shell
spread -reuse-pid=<pid> -discard
```

Implementation:

- [`Reuse`](https://github.com/canonical/spread/blob/master/spread/reuse.go)
- [Reuse file selection](https://github.com/canonical/spread/blob/master/spread/runner.go#L120-L128)
- [Server reuse and project resend logic](https://github.com/canonical/spread/blob/master/spread/runner.go#L752-L817)
- [`reuseServer`](https://github.com/canonical/spread/blob/master/spread/runner.go#L987-L1027)

## Debugging and interactive modes

The CLI supports several mutually exclusive execution modes:

- `-debug`: open an interactive shell after a script failure;
- `-shell`: open a shell instead of task execution;
- `-shell-before`: open a shell before task execution;
- `-shell-after`: open a shell after successful execution and after errors;
- `-abend`: stop at the first error without restoration;
- `-restore`: run restoration scripts only.

`-shell-before` and `-shell-after` may be used together, but they cannot be combined with the other modes above.

Interactive shells receive the job environment and a prompt containing the current backend, system, and remote path.

A common external-debugging workflow is:

```shell
spread -reuse -abend suite/task
# Connect separately to the retained worker and investigate.
spread -reuse -restore suite/task
spread -reuse -discard
```

Implementation:

- [CLI mode validation](https://github.com/canonical/spread/blob/master/cmd/spread/main.go#L54-L61)
- [Interactive shell handling](https://github.com/canonical/spread/blob/master/spread/runner.go#L438-L519)

## Main CLI reference

The `spread` executable uses Go's standard `flag` package.

| Option | Meaning |
| --- | --- |
| `-v` | Show detailed progress |
| `-vv` | Show debugging messages |
| `-list` | Print selected job names without running |
| `-pass` | Set the server root password; otherwise generate one |
| `-reuse` | Keep servers for later runs |
| `-reuse-pid` | Use state from a crashed process |
| `-resend` | Resend content to reused servers |
| `-debug` | Open a shell after script errors |
| `-shell` | Open a shell instead of running task scripts |
| `-shell-before` | Open a shell before task execution |
| `-shell-after` | Open a shell after task execution |
| `-abend` | Stop on the first error without restoring |
| `-restore` | Run restoration scripts only |
| `-discard` | Discard tracked reused servers |
| `-artifacts` | Local destination for task artifacts |
| `-seed` | Seed the job-order permutation |
| `-repeat` | Number of additional executions per task |
| `-gc` | Run provider garbage collection and exit |

`-repeat=N` performs the initial execution plus up to `N` additional executions. Repetition stops at the first failure.

Source: [`cmd/spread/main.go`](https://github.com/canonical/spread/blob/master/cmd/spread/main.go).

## Providers

All providers implement allocation, reuse, garbage collection, and server lifecycle interfaces from `spread/provider.go`. The runner communicates with allocated servers through SSH regardless of provider.

### LXD

The LXD provider launches containers through the `lxc` command.

Key behavior:

- maps Spread-style image names to `ubuntu:` or `images:` remotes;
- prefers a matching locally cached image;
- creates ephemeral containers unless `-reuse` is active;
- waits for a non-loopback IPv4 address;
- enables root password authentication in `sshd`;
- deletes containers with `lxc delete --force`;
- supports a remote name through backend `location`.

Relevant files:

- [`spread/lxd.go`](https://github.com/canonical/spread/blob/master/spread/lxd.go)
- [`spread/lxd_test.go`](https://github.com/canonical/spread/blob/master/spread/lxd_test.go)
- [LXD documentation](https://github.com/canonical/spread/blob/master/README.md#lxd-backend)

### QEMU

The QEMU provider launches local `qemu-system-x86_64` virtual machines using KVM and snapshot mode.

Images are read from:

```text
$HOME/.spread/qemu/<image>.img
```

Key behavior:

- default memory is 1500 MB and may be overridden with backend `memory`;
- randomly selects a local SSH-forwarding port;
- exposes serial and monitor consoles on nearby ports;
- uses `-nographic` unless `SPREAD_QEMU_GUI=1`;
- supports unset legacy BIOS or `bios: uefi`;
- reads custom BIOS images from `$HOME/.spread/qemu/bios/`;
- supports `SPREAD_QEMU_FALLBACK_BIOS_PATH`;
- defaults UEFI firmware to `/usr/share/OVMF/OVMF_CODE.fd`;
- stores the QEMU PID as provider reuse data.

Relevant files:

- [`spread/qemu.go`](https://github.com/canonical/spread/blob/master/spread/qemu.go)
- [`spread/qemu_test.go`](https://github.com/canonical/spread/blob/master/spread/qemu_test.go)
- [QEMU documentation](https://github.com/canonical/spread/blob/master/README.md#qemu-backend)

### Google Compute Engine

The Google provider uses the Compute Engine REST API with OAuth2 credentials.

Configuration highlights:

```yaml
backends:
    google:
        key: "$(HOST: echo "$GOOGLE_JSON_FILENAME")"
        location: project-id/zone
        halt-timeout: 2h
        systems:
            - ubuntu-24.04:
                plan: n1-standard-1
                storage: 20G
                cpu-family: Intel Skylake
                secure-boot: true
```

`key` may contain service-account JSON, name a credentials file, or be empty when Application Default Credentials are available.

Key behavior:

- finds images by exact name, family, then description terms;
- searches the configured project and known public image projects;
- creates instances with an external NAT address;
- uses metadata startup scripts to enable root SSH;
- waits for a serial-port readiness marker;
- removes the startup script after boot;
- supports machine type, storage, CPU family, and Secure Boot;
- labels Spread-created instances;
- garbage-collects instances older than `halt-timeout`.

Relevant files:

- [`spread/google.go`](https://github.com/canonical/spread/blob/master/spread/google.go)
- [`spread/google_test.go`](https://github.com/canonical/spread/blob/master/spread/google_test.go)
- [Google documentation](https://github.com/canonical/spread/blob/master/README.md#google-backend)

### OpenStack

The OpenStack provider uses `go-goose` clients for Keystone, Nova, Neutron, and Glance.

Configuration highlights:

```yaml
backends:
    openstack:
        endpoint: https://keystone.example/v3
        account: account-name
        key: "$(HOST: echo "$OS_PASSWORD")"
        location: project/region
        plan: m1.medium
        networks:
            - internal
        groups:
            - spread
        halt-timeout: 2h
        systems:
            - ubuntu-24.04
```

Key behavior:

- supports OpenStack Identity API v3;
- authenticates with username, password, project, and region;
- finds an exact image name or the newest term match;
- selects the requested flavor, networks, and security groups;
- uses the first non-external network if none is configured;
- installs a cloud-init script that enables root SSH;
- waits for a serial-console marker and falls back to SSH when serial output is unavailable;
- tags instances with Spread metadata;
- garbage-collects old Spread instances.

Relevant files:

- [`spread/openstack.go`](https://github.com/canonical/spread/blob/master/spread/openstack.go)
- [`spread/openstack_test.go`](https://github.com/canonical/spread/blob/master/spread/openstack_test.go)
- [OpenStack documentation](https://github.com/canonical/spread/blob/master/README.md#openstack-backend)

### Linode

The Linode provider is implemented against Linode's legacy API.

Key behavior:

- can adopt an unused powered-off server;
- can create an ephemeral server when plan and location permit;
- creates root and swap disks plus a boot configuration;
- resolves distributions, account images, kernels, plans, and locations;
- watches reused servers and restarts them if they power off unexpectedly;
- uses label and activity checks to reduce concurrent allocation conflicts;
- powers down and cleans reusable servers;
- removes ephemeral servers;
- garbage-collects stale resources and abandoned disks/configurations.

Important fields include `key`, `plan`, `location`, `halt-timeout`, system `image`, `kernel`, and `storage`.

Relevant files:

- [`spread/linode.go`](https://github.com/canonical/spread/blob/master/spread/linode.go)
- [Linode documentation](https://github.com/canonical/spread/blob/master/README.md#linode-backend)

### AdHoc

The AdHoc provider delegates allocation and disposal to local shell scripts.

```yaml
backends:
    custom:
        type: adhoc
        allocate: |
            address="$(allocate-machine)"
            ADDRESS "$address"
        discard: |
            discard-machine "$SPREAD_SYSTEM_ADDRESS"
        systems:
            - custom-linux
```

The allocation script must emit an address using `ADDRESS`. `FATAL` prevents retrying, while `ERROR` reports a retryable allocation failure. Spread waits for the resulting SSH endpoint before continuing.

Relevant files:

- [`spread/adhoc.go`](https://github.com/canonical/spread/blob/master/spread/adhoc.go)
- [AdHoc integration fixture](https://github.com/canonical/spread/tree/master/tests/adhoc)
- [AdHoc documentation](https://github.com/canonical/spread/blob/master/README.md#adhoc-backend)

### Humbox

Humbox is both a Spread provider and a separate HTTP service included in this repository. It manages QEMU workers behind an authenticated API.

Provider configuration uses:

```yaml
backends:
    humbox:
        key: "$(HOST: echo "$HUMBOX_TOKEN")"
        location: https://account@host:port
        systems:
            - image-name
```

The provider:

- authenticates with HTTP Basic authentication;
- creates servers through `POST /v1/servers`;
- deletes servers through `DELETE /v1/servers/<name>`;
- receives the SSH endpoint from the service;
- retries HTTP 5xx responses;
- records server metadata for reuse.

The `humbox` service:

- reads `setup.yaml` from its data directory;
- validates configured images and accounts;
- uses QEMU qcow2 overlays and cloud-init seed images;
- exposes HTTP and optional HTTPS;
- supports static certificates or ACME;
- provides `/health-check`;
- provides authenticated `/v1/servers` endpoints;
- can generate a salted BLAKE2b account token hash with `-token`.

Relevant files:

- [`spread/humbox.go`](https://github.com/canonical/spread/blob/master/spread/humbox.go)
- [`cmd/humbox/main.go`](https://github.com/canonical/spread/blob/master/cmd/humbox/main.go)
- [`cmd/humbox/manager.go`](https://github.com/canonical/spread/blob/master/cmd/humbox/manager.go)

## Repository layout

```text
.github/workflows/test.yaml  Unit and full-system CI workflow
cmd/spread/                  Main Spread CLI
cmd/humbox/                  Humbox QEMU worker service
spread/                      Core project model, runner, SSH client, and providers
spread/testutil/             Helpers used by Go tests
tests/                       Self-hosted full-system integration fixtures
README.md                    User-facing configuration and backend guide
go.mod, go.sum               Go module and dependency metadata
spread.yaml                  Spread's own full-system test configuration
snapcraft.yaml               Snap packaging definition
renovate.json                Dependency-update configuration
LICENSE                      GPLv3 license text
```

### Important core files

- [`spread/project.go`](https://github.com/canonical/spread/blob/master/spread/project.go): configuration structures, YAML loading, validation, environment evaluation, filtering, and job-matrix expansion.
- [`spread/runner.go`](https://github.com/canonical/spread/blob/master/spread/runner.go): provider setup, content packaging, worker scheduling, lifecycle execution, artifacts, reuse, and statistics.
- [`spread/client.go`](https://github.com/canonical/spread/blob/master/spread/client.go): SSH sessions, remote shell construction, script helpers, reboots, transfers, interactive shells, and timeout handling.
- [`spread/provider.go`](https://github.com/canonical/spread/blob/master/spread/provider.go): provider and server interfaces plus fatal allocation errors.
- [`spread/reuse.go`](https://github.com/canonical/spread/blob/master/spread/reuse.go): locked and recoverable YAML state for retained workers.
- [`spread/logger.go`](https://github.com/canonical/spread/blob/master/spread/logger.go): progress, timing, fold, and debug logging.
- [`spread/adhoc.go`](https://github.com/canonical/spread/blob/master/spread/adhoc.go): user-defined allocation scripts.
- [`spread/google.go`](https://github.com/canonical/spread/blob/master/spread/google.go): Google Compute Engine provider.
- [`spread/openstack.go`](https://github.com/canonical/spread/blob/master/spread/openstack.go): OpenStack provider.
- [`spread/linode.go`](https://github.com/canonical/spread/blob/master/spread/linode.go): Linode provider.
- [`spread/lxd.go`](https://github.com/canonical/spread/blob/master/spread/lxd.go): LXD provider.
- [`spread/qemu.go`](https://github.com/canonical/spread/blob/master/spread/qemu.go): local QEMU provider.
- [`spread/humbox.go`](https://github.com/canonical/spread/blob/master/spread/humbox.go): Humbox API provider.

## Tests

### Unit tests

Run all Go tests:

```shell
go test ./...
```

Run verbosely:

```shell
go test -v ./...
```

Tests use `gopkg.in/check.v1` alongside standard Go testing. Provider tests often replace package-level network or command hooks with fakes.

Notable test files:

- [`spread/project_test.go`](https://github.com/canonical/spread/blob/master/spread/project_test.go)
- [`spread/client_test.go`](https://github.com/canonical/spread/blob/master/spread/client_test.go)
- [`spread/google_test.go`](https://github.com/canonical/spread/blob/master/spread/google_test.go)
- [`spread/openstack_test.go`](https://github.com/canonical/spread/blob/master/spread/openstack_test.go)
- [`spread/lxd_test.go`](https://github.com/canonical/spread/blob/master/spread/lxd_test.go)
- [`spread/qemu_test.go`](https://github.com/canonical/spread/blob/master/spread/qemu_test.go)

### Full-system tests

The repository tests Spread with Spread. The root [`spread.yaml`](https://github.com/canonical/spread/blob/master/spread.yaml) prepares Go and virtualization dependencies, builds the Spread binary under test, and runs suites from `tests/`.

Fixture groups cover:

- `tests/adhoc`: custom allocation and disposal;
- `tests/artifacts`: artifact collection on success and failure;
- `tests/envs`: cascading environment and variants;
- `tests/lxd`: nested LXD execution;
- `tests/manual`: manual backend, system, suite, and task selection;
- `tests/match`: `MATCH`;
- `tests/nomatch`: `NOMATCH`;
- `tests/qemu`: nested QEMU execution;
- `tests/reboot`: repeated and keyed reboots;
- `tests/repack`: content repacking and resend behavior.

The GitHub Actions workflow:

1. installs Go from the Snap Store;
2. runs `go test -v ./...`;
3. builds a pinned known-stable Spread revision as the outer runner;
4. runs the current repository's integration tests on the configured Google backend;
5. always attempts to discard workers left in process-specific reuse files.

Workflow: [`.github/workflows/test.yaml`](https://github.com/canonical/spread/blob/master/.github/workflows/test.yaml).

## Development

The module declares Go 1.23 and a Go 1.24.3 toolchain.

```shell
git clone https://github.com/canonical/spread.git
cd spread

go test ./...
go build ./cmd/spread
go build ./cmd/humbox
```

Install development binaries:

```shell
go install ./cmd/spread
go install ./cmd/humbox
```

Useful focused test commands:

```shell
go test ./spread
go test -run TestName ./spread
go test -v ./spread
```

There is no repository Makefile. Standard Go commands and the root Spread configuration are the authoritative development interfaces.

Important dependencies:

- `golang.org/x/crypto`: SSH, terminal, ACME, and BLAKE2b support;
- `golang.org/x/oauth2`: Google authentication;
- `github.com/go-goose/goose/v5`: OpenStack clients;
- `gopkg.in/yaml.v2` and `gopkg.in/yaml.v3`: project, reuse, and Humbox configuration;
- `gopkg.in/tomb.v2`: runner and watcher lifecycle management;
- `gopkg.in/check.v1`: tests;
- `github.com/niemeyer/pretty`: diagnostic formatting.

Module metadata: [`go.mod`](https://github.com/canonical/spread/blob/master/go.mod).

## Packaging and release

The repository includes a strict-confinement Snap package.

The Snap:

- exposes the `spread` command;
- uses the `core24` base;
- builds with the Snapcraft Go plugin;
- plugs `home`, `network`, and `network-bind`;
- derives a version in the form `YYYY.MM.DD-g<short-commit>`.

Packaging definition: [`snapcraft.yaml`](https://github.com/canonical/spread/blob/master/snapcraft.yaml).

The documented installation path remains:

```shell
go install github.com/canonical/spread/cmd/spread@latest
```

## Guidance for code changes

When changing configuration behavior:

1. update structures and validation in `spread/project.go`;
2. verify cascade and matrix behavior in `Project.Jobs`;
3. add cases to `spread/project_test.go`;
4. add or update an integration fixture under `tests/` when behavior depends on remote execution;
5. update `README.md` if the user-facing YAML or CLI contract changes.

When changing lifecycle or scheduling:

1. inspect `Runner.loop`, `Runner.worker`, and `Runner.job`;
2. preserve the prepare/debug/restore ordering;
3. ensure restore failures prevent unsafe worker reuse;
4. preserve shared-queue locking around pending jobs, sequence numbers, reservations, statistics, and suite worker counts;
5. test repeated tasks, samples, multiple workers, and interruption cleanup.

When changing SSH or script behavior:

1. inspect `Client.run`, `Client.runPart`, and `Client.runCommand`;
2. avoid tracing environment setup because it may contain secrets;
3. preserve special exit-status handling for `REBOOT` and `ERROR`;
4. preserve stdin isolation for task scripts;
5. check interactive terminal handling and timeout behavior.

When adding a provider:

1. implement `Provider` and `Server` from `spread/provider.go`;
2. add its type to project validation in `spread/project.go`;
3. construct it in `spread.Start`;
4. provide allocation, reuse, discard, and garbage-collection behavior;
5. normalize the result to a reachable SSH endpoint;
6. store enough provider data in `Server.ReuseData` to reconnect safely;
7. classify permanent allocation errors with `FatalError`;
8. add provider unit tests and user documentation.

## Security notes

- Project and task YAML contain shell scripts and must be treated as executable code.
- `$(HOST:...)` executes locally while jobs are being constructed.
- Backend API keys and system passwords may be populated from local commands.
- Spread avoids tracing environment assignment, but scripts can still print secrets.
- SSH host keys are not verified by the current client.
- Workers are configured for password-based root access, or passwordless sudo from a configured user.
- Reuse files contain connection credentials and are created with mode `0600`.
- Cloud resources may remain allocated if cleanup is interrupted; use `-discard`, `-reuse-pid`, and provider garbage collection as appropriate.
- Google and OpenStack workers receive temporary root credentials through instance initialization metadata.
- Humbox tokens should be stored securely; the service stores salted BLAKE2b token hashes in `setup.yaml`.

## Known distinctions and cautions

- The README is the primary user guide; there is no separate `docs/` tree.
- Humbox is implemented and accepted as a backend type, but it does not have a dedicated README section comparable to the other providers.
- The Linode implementation uses the legacy `api.linode.com` API rather than the current Linode API.
- Several README examples refer to old operating-system releases. Consult provider image catalogs and current source behavior when creating new configurations.
- The module now declares a modern Go version even though a comment in `spread/client.go` still refers to compatibility with historical Go 1.6 Xenial tests.
- Backend fields are shared in `Backend` and `System`; comments in `project.go` identify which providers currently consume each field.
- `-gc` invokes every configured provider's garbage collector, but some providers intentionally implement it as a no-op.
- `-repeat=N` means one initial execution plus `N` repeats, despite the short flag description saying “number of times to repeat.”
- Job ordering is reproducible only approximately with multiple workers because workers steal from a shared pending queue according to timing.

## High-value references

- [README and complete user guide](https://github.com/canonical/spread/blob/master/README.md)
- [Main CLI](https://github.com/canonical/spread/blob/master/cmd/spread/main.go)
- [Configuration model and parser](https://github.com/canonical/spread/blob/master/spread/project.go)
- [Runner and scheduler](https://github.com/canonical/spread/blob/master/spread/runner.go)
- [SSH client and script runtime](https://github.com/canonical/spread/blob/master/spread/client.go)
- [Provider interfaces](https://github.com/canonical/spread/blob/master/spread/provider.go)
- [Reuse state](https://github.com/canonical/spread/blob/master/spread/reuse.go)
- [Repository self-test configuration](https://github.com/canonical/spread/blob/master/spread.yaml)
- [Integration fixtures](https://github.com/canonical/spread/tree/master/tests)
- [CI workflow](https://github.com/canonical/spread/blob/master/.github/workflows/test.yaml)
- [Go module](https://github.com/canonical/spread/blob/master/go.mod)
- [Snap package](https://github.com/canonical/spread/blob/master/snapcraft.yaml)
- [Humbox service](https://github.com/canonical/spread/tree/master/cmd/humbox)
