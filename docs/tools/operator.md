### Install Interface Tester

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Command to install the testing framework.

```bash
pip install pytest-interface-tester 
```

--------------------------------

### ops.pebble.Client.autostart_services

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Start the startup-enabled services and wait for them to be started.

```APIDOC
## autostart_services(timeout: float = 30.0, delay: float = 0.1) -> ChangeID

### Description
Start the startup-enabled services and wait (poll) for them to be started.

### Parameters
- **timeout** (float) - Optional - Seconds before autostart change is considered timed out.
- **delay** (float) - Optional - Seconds before executing the autostart change.
```

--------------------------------

### Configure provider test setup

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Example configuration for defining the test location and identifier in the interface repository.

```default
providers:
  - name: my-fancy-database-provider
    url: YOUR_REPO_URL
    test_setup:
      location: tests/interface/conftest.py
      identifier: database_tester
```

--------------------------------

### Define Pebble layer and start services

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Example of observing the PebbleReadyEvent to add a configuration layer and start services in a charm.

```python
# ...
import ops
# ...


class PauseCharm(ops.CharmBase):
    # ...
    def __init__(self, framework):
        super().__init__(framework)
        # Set a friendly name for your charm. This can be used with the Operator
        # framework to reference the container, add layers, or interact with
        # providers/consumers easily.
        self.name = 'pause'
        # This event is dynamically determined from the service name
        # in ops.pebble.Layer
        #
        # If you set self.name as above and use it in the layer definition following this
        # example, the event will be <self.name>_pebble_ready
        framework.observe(
            self.on.pause_pebble_ready, self._on_pause_pebble_ready
        )
        # ...

    def _on_pause_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        """Handle the pebble_ready event"""
        # You can get a reference to the container from the PebbleReadyEvent
        # directly with:
        # container = event.workload
        #
        # The preferred method is through get_container()
        container = self.unit.get_container(self.name)
        # Add our initial config layer, combining with any existing layer
        container.add_layer(self.name, self._pause_layer(), combine=True)
        # Start the services that specify 'startup: enabled'
        container.autostart()
        self.unit.status = ops.ActiveStatus()

    def _pause_layer(self) -> ops.pebble.Layer:
        """Returns Pebble configuration layer for google/pause"""
        return ops.pebble.Layer({
            'summary': 'pause layer',
            'description': 'pebble config layer for google/pause',
            'services': {
                self.name: {
                    'override': 'replace',
                    'summary': 'pause service',
                    'command': '/pause',
                    'startup': 'enabled',
                }
            },
        })


# ...
```

--------------------------------

### begin

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Instantiates the Charm and starts handling events.

```APIDOC
## begin()

### Description
Instantiate the Charm and start handling events. Before calling begin(), there is no Charm instance, so changes to the Model won't emit events.
```

--------------------------------

### start(*service_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Start given service(s) by name.

```APIDOC
## start(*service_names: str)

### Description
Start given service(s) by name.
```

--------------------------------

### begin_with_initial_hooks()

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Triggers the standard sequence of Juju startup hooks including install, relation-created, config-changed, start, and pebble-ready.

```APIDOC
## begin_with_initial_hooks()

### Description
Fires the same hooks that Juju would fire at startup. This method automatically creates peer relations specified in metadata.yaml and sets container connectivity to True for defined containers.

### Usage
`harness.begin_with_initial_hooks()`
```

--------------------------------

### Handle the install event in charm.py

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Replaces the _on_install method to install tinyproxy and report its version to Juju.

```python
    def _on_install(self, event: ops.InstallEvent) -> None:
        """Install tinyproxy on the machine."""
        if not tinyproxy.is_installed():
            tinyproxy.install()
            version = tinyproxy.get_version()
            self.unit.set_workload_version(version)
```

--------------------------------

### Implement install event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Manage package installation status and execution using Python subprocess calls.

```python
def _on_install(self, _event):
    snapinfo_cmd = Popen(
        'snap info microsample'.split(' '), stdout=subprocess.PIPE
    )
    output = check_output(
        "grep -c 'installed'".split(' '), stdin=snapinfo_cmd.stdout
    )
    is_microsample_installed = bool(output.decode('ascii').strip())

    if not is_microsample_installed:
        self.unit.status = ops.MaintenanceStatus('installing microsample')
        out = check_call('snap install microsample --edge')

    self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Handle start event

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Update the _on_start method to trigger configuration and service startup.

```python
    def _on_start(self, event: ops.StartEvent) -> None:
        """Handle start event."""
        self.configure_and_run()
```

--------------------------------

### Clone the interface repository

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Initial setup steps to clone the repository and navigate to the directory.

```bash
git clone https://github.com/canonical/charm-relation-interfaces
cd /path/to/charm-relation-interfaces
```

--------------------------------

### Install jhack

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Install the jhack snap and connect it to the Juju configuration directory.

```shell
sudo snap install jhack
sudo snap connect jhack:dot-local-share-juju snapd
```

--------------------------------

### Import path explanation

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Example of import syntax used in the charm.

```python
from charms.data_platform_libs ...
```

```python
from lib.charms.data_platform_libs...
```

--------------------------------

### Implement snap management in _on_install

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Uses the snap library to ensure the snap is installed and the service is active.

```python
def _on_install(self, _event):
    microsample_snap = snap.SnapCache()['microsample']
    if not microsample_snap.present:
        self.unit.status = ops.MaintenanceStatus('installing microsample')
        microsample_snap.ensure(snap.SnapState.Latest, channel='edge')

    self.wait_service_active()
    self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Install development tools via Concierge

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Installs Concierge and uses it to prepare the Kubernetes development environment.

```text
sudo snap install --classic concierge
sudo concierge prepare -p k8s --extra-snaps astral-uv
```

--------------------------------

### Sample output for brief logging

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Example of the console output when using the brief logging configuration.

```text
INFO jubilant cli: juju deploy --model jubilant-b3578475-test-charm ...
INFO jubilant.wait [fastapi-demo] status changed: waiting (installing agent)
INFO jubilant.wait [fastapi-demo/0] status changed: waiting (installing agent)
INFO jubilant.wait [fastapi-demo] status changed: waiting (installing agent) -> waiting (agent initialising)
INFO jubilant.wait [fastapi-demo/0] status changed: waiting (installing agent) -> waiting (agent initialising)
```

--------------------------------

### Install Concierge and dependencies

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Set up the Juju controller and required tools within the virtual machine.

```text
sudo snap install --classic concierge
sudo concierge prepare -p <preset> --extra-snaps astral-uv
```

--------------------------------

### Install ops testing framework

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Install the testing dependencies via pip or pyproject.toml.

```default
pip install ops[testing]
```

```toml
[dependency-groups]
test = [
  "ops[testing]",
]
```

--------------------------------

### Install and manage APT packages

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Use charmlibs.apt to update and install specific package versions.

```python
# src/myworkload.py
from charmlibs import apt


def install() -> None:
    apt.update()
    # Pin to a specific version so deployments are reproducible.
    apt.add_package('tinyproxy-bin', '1.11.1-3')
    # On failure, apt raises charmlibs.apt.PackageError, which puts the
    # charm into error status with a clear message in the Juju logs.


def uninstall() -> None:
    apt.remove_package('tinyproxy-bin')
```

--------------------------------

### Test Charm with Manual Setup

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Configure the model state before calling begin to avoid triggering events during initial setup.

```python
def test_bar(harness):
    # Set up model before "begin" (no events triggered)
    harness.set_leader(True)
    harness.add_relation('db', 'postgresql', unit_data={'key': 'val'})

    # Now instantiate the charm to start triggering events as the model changes
    harness.begin()
    harness.update_config({'some': 'config'})

    # Check that charm has properly handled config-changed, for example,
    # has written the app's config file
    root = harness.get_filesystem_root('container')
    assert (root / 'etc' / 'app.conf').exists()
```

--------------------------------

### Install tox and update shell

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Install tox with the uv extension and update the shell environment.

```sh
uv tool install tox --with tox-uv
uv tool update-shell
```

--------------------------------

### Action output example

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Expected output format when running the get-db-info action.

```text
Running operation 1 with 1 task
  - task 2 on unit-fastapi-demo-0

Waiting for task 2...
db-host: postgresql-k8s-primary.testing.svc.cluster.local
db-port: "5432"
```

--------------------------------

### Example streaming output logs

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Expected log output from the streaming I/O example.

```default
Output: 'one\n'
Output: '2\n'
Output: 'THREE\n'
```

--------------------------------

### Install uv on Ubuntu

Source: https://github.com/canonical/operator/blob/main/CONTRIBUTING.md

Command to install the uv package manager on Ubuntu systems.

```sh
sudo snap install astral-uv --classic
```

--------------------------------

### Initialize and start the harness with hooks

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Use this pattern to set up relations, storage, and configuration before triggering the initial charm lifecycle hooks.

```default
harness = Harness(MyCharm)
# Do initial setup here
# Add storage if needed before begin_with_initial_hooks() is called
storage_ids = harness.add_storage('data', count=1)[0]
storage_id = storage_id[0] # we only added one storage instance
harness.add_relation('db', 'postgresql', unit_data={'key': 'val'})
harness.set_leader(True)
harness.update_config({'initial': 'config'})
harness.begin_with_initial_hooks()
# This will cause
# install, db-relation-created('postgresql'), leader-elected, config-changed, start
# db-relation-joined('postgresql/0'), db-relation-changed('postgresql/0')
# To be fired.
```

--------------------------------

### Install PyYAML C speedups

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Install the libyaml-dev library to enable C speedups for PyYAML.

```sh
sudo apt-get install libyaml-dev
```

--------------------------------

### View Discovery Output

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Example output from running the interface discovery command.

```yaml
- my_fancy_database:
  - v0:
   - provider:
       - test_contract_happy_path
       - test_nothing_happens_if_remote_empty
     - schema OK
     - charms:
       - my_fancy_database_charm (https://github.com/your-github-slug/my-fancy-database-operator) custom_test_setup=no
   - requirer:
     - <no tests>
     - schema OK
     - <no charms>
```

--------------------------------

### Install tox using uv

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-charms.md

Use this command to install the tox automation tool with the tox-uv plugin for dependency management.

```bash
uv tool install tox --with tox-uv
```

--------------------------------

### Install and manage Snap packages

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Use charmlibs.snap to manage the lifecycle of snap packages.

```python
# src/myworkload.py
from charmlibs import snap


def install() -> None:
    cache = snap.SnapCache()
    workload = cache['my-workload']
    workload.ensure(snap.SnapState.Latest, channel='stable')


def start() -> None:
    snap.SnapCache()['my-workload'].start(enable=True)


def stop() -> None:
    snap.SnapCache()['my-workload'].stop(disable=True)
```

--------------------------------

### Clone the minimal charm example

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Use this command to retrieve the base code from the previous tutorial chapter.

```text
git clone https://github.com/canonical/operator.git
cd operator/examples/k8s-1-minimal
```

--------------------------------

### Tox installation warning

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Warning message regarding PATH configuration after installing tox.

```text
Installed 1 executable: tox
warning: `/home/ubuntu/.local/bin` is not on your PATH. To use installed tools,
run `export PATH="/home/ubuntu/.local/bin:$PATH"` or `uv tool update-shell`.
```

--------------------------------

### Install Linux operator libraries

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Commands to fetch the required snap and systemd libraries for the charm.

```bash
charmcraft fetch-lib charms.operator_libs_linux.v1.snap
```

```bash
charmcraft fetch-lib charms.operator_libs_linux.v0.systemd
```

--------------------------------

### start_services

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Starts the specified services and waits for them to be running.

```APIDOC
## start_services(services: Iterable[str], timeout: float = 30.0, delay: float = 0.1) -> ChangeID

### Description
Starts the specified services and polls for their status.

### Parameters
- **services** (Iterable[str]) - Required - Non-empty list of service names to start.
- **timeout** (float) - Optional - Seconds to wait for the start to complete.
- **delay** (float) - Optional - Seconds to wait before executing the start.

### Returns
- **ChangeID** - The ID of the start change operation.
```

--------------------------------

### Manual Pebble Server Configuration

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Manually start a Pebble server and run tests against it.

```sh
export PEBBLE=$HOME/pebble
export RUN_REAL_PEBBLE_TESTS=1
pebble run --create-dirs --http=:4000 &>pebble.log &

# Then
tox -e unit -- test/test_real_pebble.py
# or
source .tox/unit/bin/activate
pytest -v test/test_real_pebble.py
```

--------------------------------

### Install juju-crashdump

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Install the juju-crashdump tool via snap to generate diagnostic crash dumps.

```bash
sudo snap install --classic juju-crashdump
```

--------------------------------

### View packing output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Example of the output generated after a successful pack.

```text
Packed tinyproxy_amd64.charm
```

--------------------------------

### Validate tox installation

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Verify the tox installation and check registered plugins.

```sh
tox --version
4.26.0 from /home/<your-user>/.local/share/uv/tools/tox/lib/python3.13/site-packages/tox/__init__.py
registered plugins:
    tox-uv-1.26.0 at /home/<your-user>/.local/share/uv/tools/tox/lib/python3.13/site-packages/tox_uv/plugin.py with uv==0.7.12
```

--------------------------------

### Inspect the Pebble layer configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Example of a service definition within a rockcraft.yaml file.

```yaml
...
services:
  fastapi:
    override: replace
    summary: FastAPI demo server
    command: /bin/uvicorn api_demo_server.app:app --host 0.0.0.0 --port 8000
    startup: enabled
    environment:
      DEMO_SERVER_LOGFILE: /tmp/demo_server.log
    ...
```

--------------------------------

### Observe start event in charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-workload-version.md

Register an event handler for the start event within the charm's __init__ method.

```python
self.framework.observe(self.on.start, self._on_start)
```

--------------------------------

### Sample output for verbose logging

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Example of the console output including ISO 8601 timestamps and detailed status changes.

```text
2026-07-15T09:42:15Z INFO jubilant cli: juju deploy --model jubilant-6966ceb1-test-charm ...
2026-07-15T09:42:17Z INFO jubilant.wait [fastapi-demo] status changed: waiting (installing agent)
2026-07-15T09:42:17Z INFO jubilant.wait [fastapi-demo/0] status changed: waiting (installing agent)
2026-07-15T09:42:17Z DEBUG jubilant.wait wait: status changed:
+ .model.name = 'jubilant-6966ceb1-test-charm'
+ .model.controller = 'concierge-k8s'
+ .model.cloud = 'k8s'
+ .model.model_status.current = 'available'
+ .apps['fastapi-demo'].charm = 'local:fastapi-demo-0'
+ .apps['fastapi-demo'].charm_name = 'fastapi-demo'
+ .apps['fastapi-demo'].charm_rev = 0
+ .apps['fastapi-demo'].scale = 1
+ .apps['fastapi-demo'].app_status.current = 'waiting'
+ .apps['fastapi-demo'].app_status.message = 'installing agent'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].workload_status.current = 'waiting'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].workload_status.message = 'installing agent'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.current = 'allocating'
2026-07-15T09:42:21Z DEBUG jubilant.wait wait: status changed:
+ .apps['fastapi-demo'].provider_id = '310fb924-1932-4242-aeea-abb14a2b0cbe'
+ .apps['fastapi-demo'].address = '10.152.183.180'
2026-07-15T09:42:23Z DEBUG jubilant.wait wait: status changed:
+ .apps['fastapi-demo'].units['fastapi-demo/0'].provider_id = 'fastapi-demo-0'
2026-07-15T09:42:24Z INFO jubilant.wait [fastapi-demo] status changed: waiting (installing agent) -> waiting (agent initialising)
2026-07-15T09:42:24Z INFO jubilant.wait [fastapi-demo/0] status changed: waiting (installing agent) -> waiting (agent initialising)
2026-07-15T09:42:24Z DEBUG jubilant.wait wait: status changed:
- .apps['fastapi-demo'].app_status.message = 'installing agent'
+ .apps['fastapi-demo'].app_status.message = 'agent initialising'
- .apps['fastapi-demo'].units['fastapi-demo/0'].workload_status.message = 'installing agent'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].workload_status.message = 'agent initialising'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.version = '3.6.23'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].leader = True
+ .apps['fastapi-demo'].units['fastapi-demo/0'].address = '10.1.0.108'
```

--------------------------------

### Start and stop services

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Manage service states explicitly using start and stop methods. These operations are idempotent and handle process signals for graceful termination.

```python
class MyCharm(ops.CharmBase):
    ...

    def _on_pebble_ready(self, event):
        container = event.workload
        container.start('mysql')

    def _on_backup_action(self, event):
        container = self.unit.get_container('main')
        try:
            container.stop('mysql')
            do_mysql_backup()
            container.start('mysql')
        except ops.pebble.ProtocolError, ops.pebble.PathError, ops.pebble.ConnectionError:
            # handle Pebble errors
```

--------------------------------

### Initialize CharmBase and Observe Events

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Example of an __init__ method in a Kubernetes charm that observes a pebble_ready event and initializes a container.

```python
def __init__(self, framework: ops.Framework):
    super().__init__(framework)
    framework.observe(
        self.on['workload_container'].pebble_ready, self._on_pebble_ready
    )
    self.container = self.unit.get_container('workload-container')
```

--------------------------------

### Clone the tutorial repository

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Use these commands to retrieve the codebase from the previous tutorial chapter to begin the observability integration.

```text
git clone https://github.com/canonical/operator.git
cd operator/examples/k8s-4-action
```

--------------------------------

### Add charm library dependencies

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Install the required charmlibs-apt and charmlibs-pathops packages using uv.

```text
uv add charmlibs-apt charmlibs-pathops
```

--------------------------------

### Implement configuration and service management methods

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Methods to ensure tinyproxy is running with the correct configuration and to wait for the service to start.

```python
    def configure_and_run(self) -> None:
        """Ensure that tinyproxy is running with the correct config."""
        try:
            config = self.load_config(TinyproxyConfig)
        except pydantic.ValidationError:
            # The collect-status handler will run next and will set status for the user to see.
            return
        if not tinyproxy.is_installed():
            return
        changed = tinyproxy.ensure_config(PORT, config.slug)
        if not tinyproxy.is_running():
            tinyproxy.start()
            self.wait_for_running()
        elif changed:
            logger.info("Config changed while tinyproxy is running. Updating tinyproxy config")
            tinyproxy.reload_config()

    def wait_for_running(self) -> None:
        """Wait for tinyproxy to be running."""
        for _ in range(3):
            if tinyproxy.is_running():
                return
            time.sleep(1)
        raise RuntimeError("tinyproxy was not running within the expected time")
        # Raising a runtime error will put the charm into error status.
        # The Juju logs will show the error message, to help you debug the error.
```

--------------------------------

### Example ExecError traceback

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Traceback output when a process exits due to a signal.

```default
Traceback (most recent call last):
  ...
ops.pebble.ExecError: non-zero exit code 143 executing 'sleep'
```

--------------------------------

### Example API response

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Expected JSON output after querying the names endpoint.

```text
{"names":{"1":"maksim","2":"simon"}}
```

--------------------------------

### Manage systemd services

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Uses the systemd library to start and stop services.

```python
def _on_start(self, _event):  # noqa
    systemd.service_start('snap.microsample.microsample.service')


def _on_stop(self, _event):  # noqa
    systemd.service_stop('snap.microsample.microsample.service')
```

--------------------------------

### Initialize a Kubernetes charm project

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Use the charmcraft CLI to scaffold a new Kubernetes-based charm project.

```text
cd ~/fastapi-demo
charmcraft init --profile kubernetes
```

--------------------------------

### Example error output

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

The expected log output when a command fails.

```text
Exited with code 1. Stderr:
    cat: unrecognized option '--bad-arg'
    Try 'cat --help' for more information.
```

--------------------------------

### Integration test output example

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Expected console output after a successful integration test run.

```text
...

============================= 2 passed in 55.43s =============================
  integration: OK (57.79=setup[0.23]+cmd[57.57] seconds)
  congratulations :) (57.84 seconds)
```

--------------------------------

### Clone the tutorial repository

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Use this command to check out the code from the previous chapter of the tutorial.

```text
git clone https://github.com/canonical/operator.git
cd operator/examples/k8s-3-postgresql
```

--------------------------------

### Verify unit status after start event

Source: https://github.com/canonical/operator/blob/main/testing/README.md

A minimal test case demonstrating the basic arrange/act/assert flow using ops-scenario's Context and State objects.

```python
from ops import testing

# 'src/charm.py' typically contains the charm class.
from charm import MyCharm


def test_start():
    ctx = testing.Context(MyCharm)
    state_in = testing.State()
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == testing.ActiveStatus()
```

--------------------------------

### Define resources in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-resources.md

Example of a file resource definition within the charmcraft.yaml configuration file.

```yaml
resources:
  my-resource:
    type: file
    filename: somefile.txt
    description: test resource
```

--------------------------------

### ops.hookcmds.network_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Get network config.

```APIDOC
## ops.hookcmds.network_get(binding_name: str, *, relation_id: int | None = None)

### Description
Get network config.

### Parameters
- **binding_name** (str) - Required - A name of a binding (relation name or extra-binding name).
- **relation_id** (int) - Optional - An optional relation id to get network info for.
```

--------------------------------

### Define charm metadata

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Example of a metadata.yaml file defining a provided interface.

```yaml
provides:
  website:
    interface: http
```

--------------------------------

### start_checks(*check_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Start given check(s) by name.

```APIDOC
## start_checks(*check_names: str) -> list[str]

### Description
Start given check(s) by name. Returns a list of check names that were started.
```

--------------------------------

### Define charm metadata

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Example charmcraft.yaml configuration defining containers and peer relations.

```yaml
name: my-charm
containers:
  workload:
    resource: workload-image
peers:
  group-chat:
    interface: gossip
```

--------------------------------

### Perform a basic state-transition test

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Demonstrates a minimal test case using the Context and State objects to verify that a charm sets its status to active upon start.

```python
from ops import testing

def test_base():
    ctx = testing.Context(MyCharm)
    state = testing.State(leader=True)
    out = ctx.run(ctx.on.start(), state)
    assert out.unit_status == testing.ActiveStatus()
```

--------------------------------

### start_checks

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Starts the specified health checks.

```APIDOC
## start_checks(checks: Iterable[str]) -> list[str]

### Description
Starts the provided list of checks. Only checks that were not already running are returned.

### Parameters
- **checks** (Iterable[str]) - Required - Non-empty list of check names to start.

### Returns
- **list[str]** - A set of check names that were successfully started.
```

--------------------------------

### Implement charm event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Example of a pebble-ready event handler that writes a configuration file to a container.

```python
def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
    container = event.workload
    container.push('/etc/config.yaml', 'message: Hello, world!', make_dirs=True)
    # ...
```

--------------------------------

### Initialise a charm repository

Source: https://github.com/canonical/operator/blob/main/docs/howto/initialise-your-project.md

Use these commands to generate the recommended project structure for Kubernetes or machine charms.

```text
charmcraft init --name mega-calendar-k8s --profile kubernetes
```

```text
charmcraft init --name mega-calendar --profile machine
```

--------------------------------

### Example Test Execution Output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Sample output showing successful test execution and coverage reporting.

```text
...
============================================ test session starts =============================================
platform linux -- Python 3.12.3, pytest-8.4.1, pluggy-1.6.0 -- /home/ubuntu/fastapi-demo/.tox/unit/bin/python3
cachedir: .tox/unit/.pytest_cache
rootdir: /home/ubuntu/fastapi-demo
configfile: pyproject.toml
collected 1 item

tests/unit/test_charm.py::test_pebble_layer PASSED

============================================= 1 passed in 0.54s ==============================================
unit: commands[1]> coverage report
Name                  Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------
src/charm.py             20      0      0      0   100%
src/fastapi_demo.py       8      3      0      0    62%   35-37
-----------------------------------------------------------------
TOTAL                    28      3      0      0    89%
  unit: OK (1.91=setup[0.09]+cmd[1.54,0.28] seconds)
  congratulations :) (1.93 seconds)
```

--------------------------------

### Marking setup tests with juju_setup

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Uses the juju_setup marker to allow skipping deployment tests in subsequent runs when using --no-juju-teardown.

```python
# tests/integration/test_actions.py
import pathlib

import jubilant
import pytest

APP = 'mycharm'


@pytest.mark.juju_setup
def test_deploy(juju: jubilant.Juju, my_charm: pathlib.Path):
    juju.deploy(charm_path, APP)
    juju.wait(jubilant.all_active)
    assert ...


@pytest.mark.juju_setup
def test_some_setup_action(juju: jubilant.Juju):
    juju.run(f'{APP}/0', 'some-setup-action')
    assert ...


def test_some_repeatable_action(juju.jubilant.Juju):
    task = juju.run(f'{APP}/0', 'some-setup-action')
    assert task.results['...'] == '...'
```

--------------------------------

### Inspect Traefik service output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Example output showing the service configuration and port mappings.

```text
NAME         TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
traefik-lb   LoadBalancer   10.152.183.166   10.43.45.0    80:31471/TCP,443:31548/TCP   10m
```

--------------------------------

### Take a VM snapshot

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Create a restore point for the virtual machine from the host.

```text
exit  # Switch back to your host machine.
multipass stop juju-sandbox
multipass snapshot juju-sandbox
```

--------------------------------

### Test Pebble-ready event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Initial test setup for verifying container plans after a pebble_ready event.

```python
from ops import testing

from charm import DemoCharm


def test_pebble_ready():
    ctx = testing.Context(DemoCharm)
    container_in = testing.Container('my-container', can_connect=True)
    state_in = testing.State(containers={container_in})
    state_out = ctx.run(ctx.on.pebble_ready(container_in), state_in)
    container_out = state_out.get_container(container_in.name)
    assert 'workload' in container_out.plan.services
    assert container_out.plan.services['workload'].command == 'run-workload'
```

--------------------------------

### Execute a command and collect output

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use wait_output to run a command and retrieve its results. This example demonstrates backing up a database.

```python
process = container.exec(['pg_dump', 'mydb'], timeout=5 * 60)
sql, warnings = process.wait_output()
if warnings:
    for line in warnings.splitlines():
        logger.warning('pg_dump: %s', line.strip())
# do something with "sql"
```

--------------------------------

### Check service status before action

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use get_service and is_running to verify service state before performing operations like stopping or starting.

```python
class MyCharm(ops.CharmBase):
    ...

    def _on_backup_action(self, event):
        container = self.unit.get_container('main')
        is_running = container.get_service('mysql').is_running()
        if is_running:
            container.stop('mysql')
        do_mysql_backup()
        if is_running:
            container.start('mysql')
```

--------------------------------

### Inspect Grafana password output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Example output showing the admin password and URL path for Grafana.

```text
Running operation 3 with 1 task
  - task 4 on unit-grafana-0

Waiting for task 4...
admin-password: eEJOix1zkrJ6
url: http://10.43.45.0/cos-lite-grafana
```

--------------------------------

### Implement Machine Charm Structure

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

A complete example of a machine charm class in src/charm.py managing a Demo Server workload.

```python
#!/usr/bin/env python3
# Copyright 2025 User
# See LICENSE file for licensing details.

"""A machine charm that manages the server."""

import logging

import ops

import demo_server  # Provided by src/demo_server.py

logger = logging.getLogger(__name__)


class DemoServerCharm(ops.CharmBase):
    """Manage the server."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.start, self._on_start)

    def _on_install(self, event: ops.InstallEvent):
        """Install the server."""
        demo_server.install()

    def _on_start(self, event: ops.StartEvent):
        """Handle start event."""
        self.unit.status = ops.MaintenanceStatus('starting server')
        demo_server.start()
        version = demo_server.get_version()
        self.unit.set_workload_version(version)
        self.unit.status = ops.ActiveStatus()

    # Put helper methods here.
    # If a method doesn't depend on Ops, put it in src/demo_server.py instead.


if __name__ == '__main__':  # pragma: nocover
    ops.main(DemoServerCharm)
```

--------------------------------

### Juju status output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Example of the Juju status dashboard output.

```text
Model    Controller     Cloud/Region         Version  SLA          Timestamp
testing  concierge-lxd  localhost/localhost  3.6.11   unsupported  09:00:00+08:00
```

--------------------------------

### Define start event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-workload-version.md

Implement the event handler to retrieve the workload version and update the unit status.

```python
def _on_start(self, event: ops.StartEvent):
    # The workload exposes the version via HTTP at /version
    version = requests.get('http://localhost:8000/version').text
    self.unit.set_workload_version(version)
```

--------------------------------

### Define a single container in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Example configuration for a charm managing a single workload container.

```yaml
# ...
containers:
  pause:
    resource: pause-image

resources:
  pause-image:
    type: oci-image
    description: Docker image for google/pause
# ...
```

--------------------------------

### Navigate to project directory

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Enter the mounted project directory inside the virtual machine.

```text
cd my-charm
```

--------------------------------

### Assert workload version

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Verify that the charm reports the correct version of the installed software.

```python
    assert version == "1.11.1"  # The version installed by tinyproxy.install.
```

--------------------------------

### Initialize a machine charm project

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Use this command to create the initial directory structure and files for a machine charm.

```text
cd ~/tinyproxy
charmcraft init --profile machine
```

--------------------------------

### Implement tinyproxy helper module

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Define the helper functions for managing tinyproxy installation, configuration, and process control in src/tinyproxy.py.

```python
"""Functions for interacting with tinyproxy."""

import logging
import os
import shutil
import signal
import subprocess

from charmlibs import apt, pathops

logger = logging.getLogger(__name__)

CONFIG_FILE = pathops.LocalPath("/etc/tinyproxy/tinyproxy.conf")
PID_FILE = pathops.LocalPath("/var/run/tinyproxy.pid")


def ensure_config(port: int, slug: str) -> bool:
    """Ensure that tinyproxy is configured. Return True if any changes were made."""
    # For the config file format, see https://manpages.ubuntu.com/manpages/noble/en/man5/tinyproxy.conf.5.html
    config = f"""\
PidFile "{PID_FILE}"
Port {port}
Timeout 600
ReverseOnly Yes
ReversePath "/{slug}/" "http://www.example.com/"
"""
    return pathops.ensure_contents(CONFIG_FILE, config)


def get_version() -> str:
    """Get the version of tinyproxy that is installed."""
    result = subprocess.run(["tinyproxy", "-v"], check=True, capture_output=True, text=True)
    return result.stdout.removeprefix("tinyproxy").strip()


def install() -> None:
    """Use APT to install the tinyproxy executable."""
    apt.update()
    # Install a specific package from ubuntu@24.04
    # See https://packages.ubuntu.com/noble/tinyproxy-bin
    # In general, it's good practice for charms to pin workload versions.
    apt.add_package("tinyproxy-bin", "1.11.1-3")
    # If this call fails, the charm will go into error status. The Juju logs will show the error:
    # charmlibs.apt.PackageError: Failed to install packages: tinyproxy-bin


def is_installed() -> bool:
    """Return whether the tinyproxy executable is available."""
    return shutil.which("tinyproxy") is not None


def is_running() -> bool:
    """Return whether tinyproxy is running."""
    return bool(_get_pid())


def reload_config() -> None:
    """Ask tinyproxy to reload config."""
    pid = _get_pid()
    if not pid:
        raise RuntimeError("tinyproxy is not running")
    # Sending signal SIGUSR1 doesn't terminate the process. It asks the process to reload config.
    # See https://manpages.ubuntu.com/manpages/noble/en/man8/tinyproxy.8.html#signals
    os.kill(pid, signal.SIGUSR1)


def start() -> None:
    """Start tinyproxy."""
    subprocess.run(["tinyproxy"], check=True, capture_output=True, text=True)


def stop() -> None:
    """Stop tinyproxy."""
    pid = _get_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)


def uninstall() -> None:
    """Uninstall the tinyproxy executable and remove files."""
    apt.remove_package("tinyproxy-bin")
    PID_FILE.unlink(missing_ok=True)
    CONFIG_FILE.unlink(missing_ok=True)
    CONFIG_FILE.parent.rmdir()


def _get_pid() -> int | None:
    """Return the PID of the tinyproxy process, or None if the process can't be found."""
    if not PID_FILE.exists():
        return None
    pid = int(PID_FILE.read_text())
    try:
        # Sending signal 0 doesn't terminate the process. It just checks whether the PID exists.
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    return pid
```

--------------------------------

### Define Ingress resource

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Example Ingress configuration to expose the metrics endpoint externally.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: metrics
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  rules:
  - http:
      paths:
      - path: /my-charm/(.*)
        pathType: Prefix
        backend:
          service:
            name: my-charm
            port:
              number: 38813
```

--------------------------------

### Build documentation locally

Source: https://github.com/canonical/operator/blob/main/CONTRIBUTING.md

Commands to build or serve the documentation locally for previewing changes.

```make
make -C docs html
```

```make
make -C docs run
```

--------------------------------

### Inspect multipass info output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Example output displaying the virtual machine status and assigned IPv4 addresses.

```text
Name:           juju-sandbox-k8s
State:          Running
Snapshots:      1
IPv4:           10.112.13.157
                10.49.132.1
                10.1.157.64
Release:        Ubuntu 24.04.3 LTS
Image hash:     2b5f90ffe818 (Ubuntu 24.04 LTS)
CPU(s):         4
Load:           0.31 0.25 0.28
Disk usage:     19.4GiB out of 48.4GiB
Memory usage:   3.2GiB out of 7.7GiB
Mounts:         /home/me/k8s-tutorial => ~/fastapi-demo
                    UID map: 1000:default
                    GID map: 1000:default
```

--------------------------------

### View Juju status output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Example output showing the application in a blocked state due to an invalid configuration.

```text
Model    Controller     Cloud/Region  Version  SLA          Timestamp
testing  concierge-k8s  k8s           3.6.13   unsupported  18:19:24+01:00

App           Version  Status   Scale  Charm         Channel  Rev  Address         Exposed  Message
fastapi-demo           blocked      1  fastapi-demo             1  10.152.183.215  no       Invalid port number, 22 is reserved for SSH

Unit             Workload  Agent  Address      Ports  Message
fastapi-demo/0*  blocked   idle   10.1.157.74         Invalid port number, 22 is reserved for SSH
```

--------------------------------

### Active charm status

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Example of Juju status output when the charm is active.

```text
Model    Controller     Cloud/Region         Version  SLA          Timestamp
testing  concierge-lxd  localhost/localhost  3.6.11   unsupported  09:01:38+08:00

App        Version  Status  Scale  Charm      Channel  Rev  Exposed  Message
tinyproxy  1.11.1   active      1  tinyproxy             0  no

Unit          Workload  Agent  Machine  Public address  Ports  Message
tinyproxy/0*  active    idle   0        10.71.67.208

Machine  State    Address       Inst id        Base          AZ            Message
0        started  10.71.67.208  juju-8e7bd9-0  ubuntu@24.04  juju-sandbox  Running
```

--------------------------------

### Test charm container logic using Harness

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Example of testing charm container status and Pebble plans using the Harness testing framework.

```python
import ops
import pytest
from ops import testing

from charm import DemoCharm


def test_container():
    harness = testing.Harness(DemoCharm)

    # Check that the charm goes into active status when it starts.
    harness.begin_with_initial_hooks()  # Triggers the pebble-ready event.
    harness.evaluate_status()
    assert isinstance(harness.charm.unit.status, ops.model.ActiveStatus)

    # Check the Pebble plan in the workload container.
    plan = harness.get_container_pebble_plan('my-container')
    assert 'workload' in plan.services
    assert plan.services['workload'].command == 'run-workload'

    # Simulate a dropped connection to the container, then check the charm's status.
    harness.set_can_connect('my-container', False)
    harness.evaluate_status()
    assert isinstance(harness.charm.unit.status, ops.model.MaintenanceStatus)
    assert harness.charm.unit.status.message == 'waiting for container'

    harness.cleanup()
```

--------------------------------

### Check configuration options

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

List the available configuration options for the deployed charm.

```text
juju config fastapi-demo
```

--------------------------------

### Add Pydantic dependency

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Installs the Pydantic dependency using the uv package manager.

```text
uv add pydantic
```

--------------------------------

### get_notice(id: str) -> Notice

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Get details about a single notice by ID.

```APIDOC
## get_notice

### Description
Get details about a single notice by ID. Added in Juju version 3.4.

### Parameters
- **id** (str) - Required - The ID of the notice to retrieve.

### Errors
- **ModelError** - Raised if a notice with the given ID is not found.
```

--------------------------------

### Implement a charm class

Source: https://github.com/canonical/operator/blob/main/README.md

Example of a charm class using ops.CharmBase to observe Juju events and manage Pebble layers.

```python
import ops


class OpsExampleCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on['httpbin'].pebble_ready, self._on_httpbin_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_httpbin_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Define and start a workload using the Pebble API.

        Change this example to suit your needs. You'll need to specify the right entrypoint and
        environment configuration for your specific workload.

        Learn more about interacting with Pebble at
            https://canonical.com/juju/docs/ops/latest/reference/pebble/
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer('httpbin', self._pebble_layer, combine=True)
        # Make Pebble reevaluate its plan, ensuring any services are started if enabled.
        container.replan()
        # Learn more about statuses at
        # https://documentation.ubuntu.com/juju/3.6/reference/status/
        self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Initialize a charm project

Source: https://github.com/canonical/operator/blob/main/README.md

Commands to create a new directory and initialize the standard charm file structure.

```shell-script
mkdir ops-example
cd ops-example
charmcraft init
```

--------------------------------

### Execute Prometheus query

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Example PromQL expression to filter request metrics for a specific endpoint.

```text
starlette_requests_total{path="/names"}
```

--------------------------------

### Test DemoCharm with Harness

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

An example test suite using the Harness framework to verify relation data updates and action outputs.

```python
import pytest
from ops import testing

from charm import DemoCharm


def test_db_endpoint(monkeypatch: pytest.MonkeyPatch):
    harness = testing.Harness(DemoCharm)

    # Prepare the charm with initial relation data.
    relation_id = harness.add_relation('database', 'postgresql')
    harness.update_relation_data(
        relation_id,
        'postgresql',
        {'endpoints': 'foo.local:1234'},
    )
    harness.begin_with_initial_hooks()

    # Prepare a mock workload object with matching config, assuming we've
    # defined a MockWorkload class with suitable attributes and methods.
    workload = MockWorkload('foo.local:1234')
    monkeypatch.setattr(
        'charm.DemoCharm.write_workload_config', workload.write_config
    )

    # Update the relation data and check that the charm wrote new workload config.
    harness.update_relation_data(
        relation_id,
        'postgresql',
        {'endpoints': 'bar.local:5678'},
    )
    assert workload.config == 'bar.local:5678'

    # Check that the action returns the expected database endpoint.
    output = harness.run_action('get-db-endpoint')
    assert output.results == {'endpoint': 'bar.local:5678'}

    harness.cleanup()
```

--------------------------------

### Example Juju status output

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Expected output showing active status and established relations.

```text
Model    Controller     Cloud/Region  Version  SLA          Timestamp
testing  concierge-k8s  k8s           3.6.13   unsupported  13:50:39+01:00

App             Version  Status  Scale  Charm           Channel    Rev  Address         Exposed  Message
fastapi-demo             active      1  fastapi-demo                 2  10.152.183.233  no
postgresql-k8s  14.15    active      1  postgresql-k8s  14/stable  495  10.152.183.195  no

Unit               Workload  Agent  Address      Ports  Message
fastapi-demo/0*    active    idle   10.1.157.90
postgresql-k8s/0*  active    idle   10.1.157.92         Primary

Integration provider           Requirer                       Interface          Type     Message
postgresql-k8s:database        fastapi-demo:database          postgresql_client  regular
postgresql-k8s:database-peers  postgresql-k8s:database-peers  postgresql_peers   peer
postgresql-k8s:restart         postgresql-k8s:restart         rolling_op         peer
postgresql-k8s:upgrade         postgresql-k8s:upgrade         upgrade            peer
```

--------------------------------

### Fetch example.com via tinyproxy

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Use curl to verify the proxy is running on the machine address at port 8000.

```text
curl <address>:8000/example/
```

--------------------------------

### replan_services(timeout: float = 30.0, delay: float = 0.1) -> ChangeID

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Replan by (re)starting changed and startup-enabled services and checks.

```APIDOC
## replan_services(timeout=30.0, delay=0.1)

### Description
Replan by (re)starting changed and startup-enabled services and checks. After requesting the replan, also wait for any impacted services to start.

### Parameters
- **timeout** (float) - Optional - Seconds before replan change is considered timed out.
- **delay** (float) - Optional - Seconds before executing the replan change.

### Returns
- **ChangeID** - The ID of the replan change.
```

--------------------------------

### ops.main(charm_class, use_juju_for_storage=None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-main-entrypoint.rst

Initializes the charm class and dispatches the observed event. This is the standard entry point for charm execution.

```APIDOC
## ops.main(charm_class: type, use_juju_for_storage: bool | None = None)

### Description
Sets up the charm and dispatches the observed event. This function is the recommended way to start a charm.

### Parameters
- **charm_class** (type) - Required - The charm class to instantiate and receive the event.
- **use_juju_for_storage** (bool | None) - Optional - Whether to use controller-side storage. Defaults to False for most charms.

### Usage Example
```python
import ops

class SomeCharm(ops.CharmBase): ...

if __name__ == "__main__":
    ops.main(SomeCharm)
```
```

--------------------------------

### Implement start and stop event handlers

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Control system services using subprocess calls within event handlers.

```python
def _on_start(self, _event):  # noqa
    check_call(
        'systemctl start snap.microsample.microsample.service'.split(' ')
    )


def _on_stop(self, _event):  # noqa
    check_call('systemctl stop snap.microsample.microsample.service'.split(' '))
```

--------------------------------

### get_service(service_name: str) -> ServiceInfo

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Get status information for a single named service.

```APIDOC
## get_service

### Description
Get status information for a single named service.

### Parameters
- **service_name** (str) - Required - The name of the service to query.

### Errors
- **ModelError** - Raised if a service with the given name is not found.
```

--------------------------------

### Create project directory

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Creates a directory on the host machine for charm development.

```text
mkdir ~/k8s-tutorial
```

--------------------------------

### Replan a container configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use replan to apply configuration layers and start services marked as enabled. This action is used to control when service restarts occur.

```python
class SnappassTestCharm(ops.CharmBase):
    ...

    def _start_snappass(self):
        container = self.unit.containers['snappass']
        snappass_layer = {
            'services': {
                'snappass': {
                    'override': 'replace',
                    'summary': 'snappass service',
                    'command': 'snappass',
                    'startup': 'enabled',
                }
            },
        }
        container.add_layer('snappass', snappass_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Charmcraft warning message

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Example of a warning message that may appear during library fetching, which can be safely ignored.

```text
WARNING: Cannot get a keyring. Every store interaction that requires authentication will require you to log in again.
```

--------------------------------

### Implement stateless configuration change handling

Source: https://github.com/canonical/operator/blob/main/docs/explanation/storedstate-guidance.md

Demonstrates reading and writing configuration to a file instead of using StoredState to track changes.

```python
def _on_config_changed(self, event: ops.ConfigChangedEvent):
    mode = self.config['mode']
    if mode not in ('production', 'test'):
        self.unit.status = ops.BlockedStatus(f'Invalid mode: {mode!r})
        return

    with open('/etc/example_blog/mode') as mode_file:
        prev_mode = mode_file.read().strip()
    if mode == prev_mode:
        return

    with open('/etc/example_blog/mode', 'w') as mode_file:
        mode_file.write(f'{mode}\n')

    self._restart()
```

--------------------------------

### Observe relation-joined event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Register an event handler for the relation-joined event to perform setup for individual units.

```python
framework.observe(self.on.smtp_relation_joined, self._on_smtp_relation_joined)
```

--------------------------------

### Define Tracing Interface Databag Structure

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Example YAML representation of the tracing interface databag.

```yaml
# unit_data: <empty>
application_data:
  receivers:
    - protocol:
        name: otlp_http
        type: http
      url: http://traefik_address:2331
    - protocol:
        name: otlp_grpc
        type: grpc
      url: traefik_address:2331
```

--------------------------------

### Test Charm with Initial Hooks

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Trigger startup events and verify charm behavior after configuration updates using begin_with_initial_hooks.

```python
def test_foo(harness):
    # Instantiate the charm and trigger events that Juju would on startup
    harness.begin_with_initial_hooks()

    # Update charm config and trigger config-changed
    harness.update_config({'log_level': 'warn'})

    # Check that charm properly handled config-changed, for example,
    # the charm added the correct Pebble layer
    plan = harness.get_container_pebble_plan('prometheus')
    assert '--log.level=warn' in plan.services['prometheus'].command
```

--------------------------------

### Test peer relation change

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Example of using State.from_context to initialize state based on charm metadata for testing relation events.

```python
def test_peer_changed():
    ctx = testing.Context(MyCharm)
    # We can pass in all of the arguments for `State()` as well.
    state_in = testing.State.from_context(ctx, leader=True)
    rel_in = state_in.get_relations('group-chat')[0]
    state_out = ctx.run(ctx.on.relation_changed(rel), state_in)
    rel_out = state_out.get_relation(rel.in)
    assert rel_out.peers_data...
```

--------------------------------

### Deploy a bundle

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Demonstrates deploying a bundle containing the charm under test using a temporary file.

```python
def test_deploy_bundle(charm: pathlib.Path, juju: jubilant.Juju):
    # Bundle definition with the charm under test:
    bundle_yaml = f"""

bundle: kubernetes
applications:
  ca:
    charm: self-signed-certificates
    channel: edge
    scale: 1
  my-app:
    charm: ./{charm}
    ...
relations:
- - ca:certificates
  - my-app:certificates

    """.strip()

    # Note that Juju from a snap doesn't have access to /tmp.
    with NamedTemporaryFile(dir='.') as f:
        f.write(bundle_yaml)
        f.flush()
        juju.deploy(f.name)

    juju.wait(jubilant.all_active)
```

--------------------------------

### Pack and deploy the httpbin-demo charm

Source: https://github.com/canonical/operator/blob/main/examples/README.md

Commands to package the charm and deploy it to Juju with a specific resource image.

```bash
charmcraft pack
juju deploy ./httpbin-demo_amd64.charm --resource httpbin-image=kennethreitz/httpbin
```

--------------------------------

### Define the pebble-ready event handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Implement the logic to start the workload service using the Pebble API and set the charm status to active.

```python
def _on_demo_server_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
    """Define and start a workload using the Pebble API."""
    # Get a reference the container attribute on the PebbleReadyEvent
    container = event.workload
    # Start the service defined by the Pebble layer in the application image.
    container.replan()
    # Learn more about statuses at
    # https://documentation.ubuntu.com/juju/3.6/reference/status/
    self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Create a virtual machine with Multipass

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Initialize a virtual machine environment for Juju testing.

```text
multipass launch --cpus 4 --memory 8G --disk 50G --name juju-sandbox 24.04
multipass shell juju-sandbox  # Switch to your virtual machine.
```

--------------------------------

### Access metrics endpoint URL

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Example URL format for accessing the metrics endpoint within a Kubernetes cluster.

```text
my-charm-endpoints.test.svc.cluster.local:38813/v1/metrics
```

--------------------------------

### Initialize CharmBase and observe events

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Set up the charm class by observing lifecycle events in the constructor.

```python
class Microsample(ops.CharmBase):
    def __init__(self, framework):
        super().__init__(framework)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(self.on.start, self._on_start)
        # etc ...
```

--------------------------------

### Initialize interface test directory

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Create the directory and file structure required for interface testing.

```shell
mkdir ./tests/interface
touch ./tests/interface/conftest.py
```

--------------------------------

### Define Requirer Application Data

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Example of the JSON-encoded list of tables published by the requirer in the application databag.

```yaml
application_data: {
   "tables": "{ref}`'users', 'passwords']"
}
```

--------------------------------

### Create Test Module

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Initializes the test file within the interface_tests directory.

```bash
touch ./interfaces/my_fancy_database/interface_tests/test_provider.py
```

--------------------------------

### Implement holistic relation handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Example of a handler that checks for relation existence and processes secret data from the relation databag.

```python
def _update_configuration(self, _: ops.Eventbase):
    # This handles secret-changed and relation-changed.
    db_relation = self.model.get_relation('db')
    if not db_relation:
        # We're not integrated with the database charm yet.
        return
    data = db_relation.load(DatabaseProviderAppData, self.app)
    secret_id = data.credentials
    if not secret_id:
        # The credentials haven't been added to the relation by the remote app yet.
        return
    secret_contents = self.model.get_secret(id=secret_id).get_contents(
        refresh=True
    )
    self.push_configuration(
        username=secret['username'],
        password=secret['password'],
    )
```

--------------------------------

### Legacy credential retrieval in observer charms

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Example of retrieving credentials directly from relation data before the introduction of Juju secrets.

```python
class MyWebserverCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(
            self.on.database_relation_changed,
            self._on_database_relation_changed,
        )

    ...  # other methods and event handlers

    def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
        username = event.relation.data[event.app]['username']
        password = event.relation.data[event.app]['password']
        self._configure_db_credentials(username, password)
```

--------------------------------

### Conventional Commit PR Titles

Source: https://github.com/canonical/operator/blob/main/CONTRIBUTING.md

Examples of pull request titles following the conventional commit style.

```text
feat: add the ability to observe change-updated events
fix!: correct the type hinting for config data
docs: clarify how to use mounts in ops.testing.Container
ci: adjust the workflow that publishes ops-scenario
```

--------------------------------

### Define Provider Application and Unit Data

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Example of the endpoint URL and secret IDs published by the provider in the application and unit databags.

```json
application_data: {
   "api_endpoint": "https://foo.com/query"
},
units_data : {
  "my_fancy_unit/0": {
     "secret_id": "secret:12312321321312312332312323"
  },
  "my_fancy_unit/1": {
     "secret_id": "secret:45646545645645645646545456"
  }
}
```

--------------------------------

### Observe test failure output

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Example of the error output when a state-transition test fails due to missing container state.

```text
FAILED tests/unit/test_charm.py::test_get_value_action -
scenario.errors.UncaughtCharmError: Uncaught RuntimeError in charm, ...
```

--------------------------------

### Initialize MetricsEndpointProvider

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Configure the metrics provider in the charm's __init__ method to allow scraping based on configuration changes.

```python
# Provide a metrics endpoint for Prometheus to scrape.
try:
    config = self.load_config(FastAPIConfig)
except ValueError as e:
    logger.warning("Unable to add metrics: invalid configuration: %s", e)
else:
    self._prometheus_scraping = MetricsEndpointProvider(
        self,
        relation_name="metrics-endpoint",
        jobs=[{"static_configs": [{"targets": [f"*:{config.server_port}"]}]}],
        refresh_event=self.on.config_changed,
    )
```

--------------------------------

### Implement delta-based event handlers in a Juju charm

Source: https://github.com/canonical/operator/blob/main/docs/explanation/holistic-vs-delta-charms.md

This example demonstrates mapping Juju and custom events to specific handler methods within a charm class.

```python
def __init__(self, framework: ops.Framework):
    super().__init__(framework)
    self.workload = Workload()
    self.framework.observe(self.on.install, self._on_install)
    self.framework.observe(self.on.start, self._on_start)

    hostname = socket.getfqdn()
    self.foo_requirer = FooRequirer(self, 'foo-relation', address=hostname)
    self.framework.observe(
        self.foo_requirer.on.data_available,
        self._on_data_available,
    )

    self.bar_provider = BarProvider(self, 'bar-relation')
    self.framework.observe(
        self.bar_provider.on.create_bar,
        self._on_create_bar,
    )


def _on_install(self, event: ops.InstallEvent):
    self.workload.install_binaries()


def _on_start(self, event: ops.StartEvent):
    self.workload.start_service()
    # Peer relation is now usable
    if self.unit.is_leader():
        ...


def _on_data_available(self, event: DataAvailableEvent):
    # Update the workload with event's data
    self.workload.reconfigure(some_key=event.some_value)


def _on_create_bar(self, event: CreateBarEvent):
    # Provision a `Bar` resource in the workload
    self.workload.create_bar(event.some_field)
```

--------------------------------

### Pull remote paths to local system

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Demonstrates various ways to pull files and directories, including handling wildcards and multiple paths.

```default
# copy one file
container.pull_path('/foo/foobar.txt', '/dst')
# Destination results: /dst/foobar.txt

# copy a directory
container.pull_path('/foo', '/dst')
# Destination results: /dst/foo/bar/baz.txt, /dst/foo/foobar.txt

# copy a directory's contents
container.pull_path('/foo/*', '/dst')
# Destination results: /dst/bar/baz.txt, /dst/foobar.txt

# copy multiple files
container.pull_path(['/foo/bar/baz.txt', 'quux.txt'], '/dst')
# Destination results: /dst/baz.txt, /dst/quux.txt

# copy a file and a directory
container.pull_path(['/foo/bar', '/quux.txt'], '/dst')
# Destination results: /dst/bar/baz.txt, /dst/quux.txt
```

--------------------------------

### Execute with command options

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Configure execution parameters such as environment variables, working directory, and user/group permissions.

```python
process = container.exec(
    ['/bin/sh', '-c', 'echo HOME=$HOME, PWD=$PWD, FOO=$FOO'],
    environment={'FOO': 'bar'},
    working_dir='/tmp',
    timeout=5.0,
    user='bob',
    group='staff',
)
stdout, _ = process.wait_output()
logger.info('Output: %r', stdout)
```

--------------------------------

### Provide State components as sets

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

State components like containers and relations are now frozensets to ensure immutability, requiring the use of get methods for retrieval.

```python
# Older Scenario code.
state_in = State(containers=[c1, c2], relations=[r1, r2])
...
assert state_out.containers[1]...
assert state_out.relations[0]...
state_out.relations.append(r3)  # Not recommended!

# Scenario 7.x
state_in = State(containers={c1, c2}, relations={r1, r2})
...
assert state_out.get_container(c2.name)...
assert state_out.get_relation(id=r1.id)...
new_state = dataclasses.replace(state_out, relations=state_out.relations + {r3})
```

--------------------------------

### Legacy secret handling in charms

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Example of storing sensitive data directly in relation data before the introduction of Juju secrets.

```python
class MyDatabaseCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(
            self.on.database_relation_joined, self._on_database_relation_joined
        )

    ...  # other methods and event handlers

    def _on_database_relation_joined(self, event: ops.RelationJoinedEvent):
        event.relation.data[self.app]['username'] = 'admin'
        event.relation.data[self.app]['password'] = (
            'admin'  # don't do this at home
        )
```

--------------------------------

### Configure CI workflow for linting and unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/set-up-continuous-integration-for-a-charm.md

Create a .github/workflows/ci.yaml file to automate testing using tox and uv.

```yaml
name: Charm tests
on:
  push:
    branches:
      - main
  pull_request:
  workflow_call:
  workflow_dispatch:

permissions: {}

jobs:
  lint:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Set up uv
        uses: astral-sh/setup-uv@cec208311dfd045dd5311c1add060b2062131d57  # v8.0.0
      - name: Set up tox and tox-uv
        run: uv tool install tox --with tox-uv
      - name: Lint the code
        run: tox -e lint

  unit:
    name: Unit tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Set up uv
        uses: astral-sh/setup-uv@cec208311dfd045dd5311c1add060b2062131d57  # v8.0.0
      - name: Set up tox and tox-uv
        run: uv tool install tox --with tox-uv
      - name: Run unit tests
        run: tox -e unit
```

--------------------------------

### Run Development and Testing Tasks

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Standard commands for linting, formatting, testing, and documentation generation using tox and make.

```sh
# Run linting and unit tests
tox

# Run tests, specifying whole suite or specific files
tox -e unit
tox -e unit -- test/test_charm.py

# Format the code using Ruff
tox -e format

# Generate a local copy of the Sphinx docs in docs/_build
make -C docs html

# Check spelling in the doc source files
make -C docs spelling

# run only tests matching a certain pattern
tox -e unit -- -k <pattern>
```

--------------------------------

### Test invalid charm configurations

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Validates that the charm enters a BlockedStatus when provided with invalid configuration values during start or config-changed events.

```python
@pytest.mark.parametrize("invalid_slug", ["", "foo_bar", "foo/bar"])
def test_start_invalid_config(tinyproxy_installed: MockTinyproxy, invalid_slug: str):
    """Test that the charm fails to start if the config is invalid."""
    ctx = testing.Context(TinyproxyCharm)
    state_in = testing.State(config={"slug": invalid_slug})
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        f"Invalid slug: '{invalid_slug}'. Slug must match the regex [a-z0-9-]+"
    )
    assert not tinyproxy_installed.is_running()
    assert tinyproxy_installed.config is None
```

```python
@pytest.mark.parametrize("invalid_slug", ["", "foo_bar", "foo/bar"])
def test_config_changed_invalid_config(tinyproxy_configured: MockTinyproxy, invalid_slug: str):
    """Test that the charm fails to change config if the config is invalid."""
    ctx = testing.Context(TinyproxyCharm)
    state_in = testing.State(config={"slug": invalid_slug})
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        f"Invalid slug: '{invalid_slug}'. Slug must match the regex [a-z0-9-]+"
    )
    assert tinyproxy_configured.is_running()  # tinyproxy should still be running...
    assert tinyproxy_configured.config == (PORT, "example")  # ...with the original config.
    assert not tinyproxy_configured.reloaded_config
```

--------------------------------

### Deploy charm with configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Use the Juju CLI to deploy the charm using the previously defined configuration file.

```bash
juju deploy <charm-name> --config metrics-config.yaml
```

--------------------------------

### Write integration tests for charms

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Integration tests deploy the packed charm to a Juju model to verify installation, startup, and behavior using pytest-jubilant.

```python
# tests/integration/test_charm.py
import pathlib

import jubilant
import pytest


@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    juju.deploy(charm, app='myworkload')
    juju.wait(jubilant.all_active, timeout=600)


def test_workload_version(juju: jubilant.Juju):
    version = juju.status().apps['myworkload'].version
    assert (
        version == '1.11.1'
    )  # The version we pinned in install(), as reported by the workload.


def test_blocks_on_invalid_config(juju: jubilant.Juju):
    juju.config('myworkload', {'slug': 'not/valid'})
    juju.wait(jubilant.all_blocked)
    juju.config('myworkload', reset='slug')
```

--------------------------------

### Fetch charm libraries

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Run the charmcraft command to download the specified libraries into the project.

```text
ubuntu@juju-sandbox-k8s:~/fastapi-demo$ charmcraft fetch-libs
```

--------------------------------

### Import Prometheus library

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Include the MetricsEndpointProvider library at the top of your charm.py file.

```python
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
```

--------------------------------

### Perform comprehensive charm state testing

Source: https://github.com/canonical/operator/blob/main/testing/README.md

A complex test example utilizing pytest parametrization to verify charm behavior across different leader states, including relations, secrets, and container configurations.

```python
import pytest
from ops import testing

from charm import MyCharm


@pytest.mark.parametrize(
    'leader',
    [pytest.param(True, id='leader'), pytest.param(False, id='non-leader')],
)
def test_(leader: bool):
    # Arrange:
    ctx = testing.Context(MyCharm)
    relation = testing.Relation('db', local_app_data={'hostname': 'example.com'})
    peer_relation = testing.PeerRelation('peer')
    container = testing.Container('workload', can_connect=True)
    relation_secret = testing.Secret({'certificate': 'xxxxxxxx'})
    user_secret = testing.Secret({'username': 'admin', 'password': 'xxxxxxxx'})
    config = {'port': 8443, 'admin-credentials': 'secret:1234'}
    state_in = testing.State(
        leader=leader,
        config=config,
        relations={relation, peer_relation},
        containers={container},
        secrets={relation_secret, user_secret},
        unit_status=testing.BlockedStatus(),
        workload_version='1.0.1',
    )

    # Act:
    state_out = ctx.run(ctx.on.relation_changed(relation), state_in)

    # Assert:
    assert testing.JujuLogLine(level='INFO', message='Distributing secret.') in ctx.juju_log
    peer_relation_out = state_out.get_relation(peer_relation.id)
    assert peer_relation_out.peers_data[0] == {'secret_id': relation_secret.id}
```

--------------------------------

### Exercise a charm with integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Demonstrates deploying charms, creating integrations, waiting for active states, and running actions.

```python
def test_integrate(charm: pathlib.Path, juju: jubilant.Juju):
    # Deploy some other charm from Charmhub:
    juju.deploy('other-app')

    # Integrate the charms:
    juju.integrate('your-app:endpoint1', 'other-app:endpoint2')

    # Ensure that both applications and all units reach a good state:
    juju.wait(jubilant.all_active)

    # Run an action on a unit:
    result = juju.run('your-app/0', 'some-action')
    assert result.results['key'] == 'value'

    # What this means depends on the workload:
    assert charm_operates_correctly()
```

--------------------------------

### Snapshot virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Creates a restore point for the virtual machine.

```text
multipass snapshot juju-sandbox
```

--------------------------------

### make_dir(path: str | PurePath, *, make_parents: bool = False, permissions: int | None = None, user_id: int | None = None, user: str | None = None, group_id: int | None = None, group: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Create a directory on the remote system with the given attributes.

```APIDOC
## make_dir

### Description
Create a directory on the remote system with the given attributes.

### Parameters
- **path** (str | PurePath) - Required - Path of the directory to create.
- **make_parents** (bool) - Optional - If true, create parent directories if they don't exist.
- **permissions** (int) - Optional - Permissions (mode) to create directory with.
- **user_id** (int) - Optional - User ID (UID) for directory.
- **user** (str) - Optional - Username for directory.
- **group_id** (int) - Optional - Group ID (GID) for directory.
- **group** (str) - Optional - Group name for directory.
```

--------------------------------

### Get Traefik load balancer service details

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Retrieve the Kubernetes service information to identify the external port used by the load balancer.

```text
kubectl -n cos-lite get svc traefik-lb
```

--------------------------------

### Verify virtual machine launch

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Confirmation message displayed after successful VM creation.

```text
Launched: juju-sandbox-k8s
```

--------------------------------

### Retrieving secret content in observer charms

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Example of using a secret ID from relation data to fetch and access secret content via the Juju model.

```python
class MyWebserverCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(
            self.on.database_relation_changed,
            self._on_database_relation_changed,
        )

    ...  # other methods and event handlers

    def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
        secret_id = event.relation.data[event.app]['secret-id']
        secret = self.model.get_secret(id=secret_id)
        content = secret.get_content()
        self._configure_db_credentials(content['username'], content['password'])
```

--------------------------------

### Execute with service context

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Inherit environment and user settings from an existing service definition.

```python
# Use environment, user/group, and working_dir from "database" service
process = container.exec(['pg_dump', 'mydb'], service_context='database')
process.wait_output()
```

--------------------------------

### Configure Pebble health checks in YAML

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Define health checks within the layer configuration using the checks field. This example demonstrates the syntax for exec, tcp, and http check types.

```yaml
checks:
    up:
        override: replace
        level: alive  # optional, but required for liveness/readiness probes
        period: 10s   # this is the default
        timeout: 3s   # this is the default
        threshold: 3  # this is the default
        exec:
            command: service nginx status

    online:
        override: replace
        level: ready
        tcp:
            port: 8080

    http-test:
        override: replace
        http:
            url: http://localhost:8080/test
```

--------------------------------

### Set and get data from peer relation databag

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Access the peer relation databag within charm event handlers to persist and retrieve application data.

```python
def _on_start(self, event: ops.StartEvent):
    peer = self.model.get_relation('charm-peer')
    peer.data[self.app]['expensive-value'] = self._calculate_expensive_value()


def _on_stop(self, event: ops.StopEvent):
    peer = self.model.get_relation('charm-peer')
    logger.info('Value at stop is: %s', peer.data[self.app]['expensive-value'])
```

--------------------------------

### Set tracing destination with ops.tracing.set_destination

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Use this function to manually specify a tracing destination when the default relation databag setup is insufficient. It is safe to call unconditionally in a reconciler pattern as repeated calls with identical arguments are no-ops.

```python
ops.tracing.set_destination(url, ca)
```

--------------------------------

### Run the charm listing review tool

Source: https://github.com/canonical/operator/blob/main/docs/howto/make-your-charm-discoverable.md

Execute this command in the root of your charm repository to check against public listing requirements.

```bash
uvx charmhub-listing-review:self-review
```

--------------------------------

### Enter Virtual Environment for Debugging

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Commands to sync dependencies and activate the virtual environment for direct tool execution.

```sh
uv sync --all-groups
source .venv/bin/activate
pytest
```

--------------------------------

### ops.main.main(charm_class, use_juju_for_storage=None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-main-entrypoint.rst

Legacy entry point for initializing a charm. This method is deprecated in favor of ops.main().

```APIDOC
## ops.main.main(charm_class: type, use_juju_for_storage: bool | None = None)

### Description
Legacy entrypoint to set up the charm and dispatch the observed event. 

### Deprecation Notice
Deprecated since version 2.16.0: This entrypoint has been deprecated, use ops.main() instead.

### Parameters
- **charm_class** (type) - Required - The charm class to instantiate and receive the event.
- **use_juju_for_storage** (bool | None) - Optional - Whether to use controller-side storage.
```

--------------------------------

### Define charm and import testing framework

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Create a placeholder charm class and import the necessary testing modules.

```python
class MyCharm(ops.CharmBase):
    pass
```

```python
import ops
from ops import testing
```

--------------------------------

### replan()

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Replan all services.

```APIDOC
## replan()

### Description
Replan all services: restart changed services and start startup-enabled services.
```

--------------------------------

### Copy the interface template

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Create a new interface directory by copying the existing template.

```bash
cp -r ./interfaces/__template__ ./interfaces/my_fancy_database
```

--------------------------------

### Initialize GrafanaDashboardProvider

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Instantiate the provider within the charm's __init__ method using the relation name defined in charmcraft.yaml.

```python
# Provide grafana dashboards over a relation interface.
self._grafana_dashboards = GrafanaDashboardProvider(
    self, relation_name="grafana-dashboard"
)
```

--------------------------------

### Pack the charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Combines charm code and metadata into a deployable file.

```text
charmcraft pack
```

--------------------------------

### Deploy with resources via CLI

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-resources.md

Override published resources during development by specifying local file paths at deployment time.

```text
echo "TEST" > /tmp/somefile.txt
charmcraft pack
juju deploy ./my-charm.charm --resource my-resource=/tmp/somefile.txt
```

--------------------------------

### Structure a charm with event observation and reconciliation

Source: https://github.com/canonical/operator/blob/main/docs/explanation/holistic-vs-delta-charms.md

Shows how to initialize charm components and observe events to trigger the reconciliation loop, including early readiness checks.

```python
def __init__(self, framework: ops.Framework):
    super().__init__(framework)
    self.typed_config = self.load_config(ConfigClass, errors='blocked')
    self.workload = Workload()
    self.foo_requirer = FooRequirer()
    self.bar_provider = BarProvider()

    events = [
        self.on.start,
        self.on.config_changed,
        self.on['foo-relation'].relation_changed,
        self.on['bar-relation'].relation_changed,
        ...,
    ]

    for event in events:
        framework.observe(event, self._reconcile)


def _reconcile(self, _: ops.EventBase):
    # Early checks
    workload_ready = self.workload.is_ready
    foo_ready = self.foo_requirer.is_ready
    bar_ready = self.bar_provider.is_ready

    if not workload_ready or not foo_ready or not bar_ready:
        # Status will be set in `_on_collect_unit_status`
        return

    try:
        # 1. Read the inputs: configuration, libraries and the workload
        # 2. Compute the new state
        # 3. Write the outputs to the libraries and the workload
        ...
    except (WorkloadError, FooError, BarError, ops.ModelError, ...):
        # Error handling
        ...
```

--------------------------------

### Stop and snapshot the virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Stops the VM and creates a snapshot for backup purposes.

```text
multipass stop juju-sandbox-k8s
multipass snapshot juju-sandbox-k8s
```

--------------------------------

### List charm directory structure

Source: https://github.com/canonical/operator/blob/main/README.md

Displays the generated file structure after running charmcraft init.

```shell-script
$ ls -R
.:
CONTRIBUTING.md  README.md        pyproject.toml    src    tox.ini
LICENSE          charmcraft.yaml  requirements.txt  tests

./src:
charm.py

./tests:
integration  unit

./tests/integration:
test_charm.py

./tests/unit:
test_charm.py
```

--------------------------------

### Action output with parameters

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Expected output when the show-password parameter is set to True.

```text
Running operation 3 with 1 task
  - task 4 on unit-fastapi-demo-0

Waiting for task 4...
db-host: postgresql-k8s-primary.testing.svc.cluster.local
db-password: RGv80aF9WAJJtExn
db-port: "5432"
db-username: relation_id_4
```

--------------------------------

### Define and run a charm on the fly

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Use testing.Context to define a charm class and execute a state transition without external files.

```python
class MyCharmType(ops.CharmBase):
    pass


ctx = testing.Context(charm_type=MyCharmType, meta={'name': 'my-charm-name'})
ctx.run(ctx.on.start(), testing.State())
```

--------------------------------

### Mount project directory

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Mounts the host project directory into the virtual machine.

```text
multipass mount --type native ~/k8s-tutorial juju-sandbox-k8s:~/fastapi-demo
```

--------------------------------

### Initialize a charm with ops.main

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-main-entrypoint.rst

Standard implementation pattern for defining a charm class and invoking the main entry point within the execution block.

```python
import ops

class SomeCharm(ops.CharmBase): ...

if __name__ == "__main__":
    ops.main(SomeCharm)
```

--------------------------------

### Invoke action with parameters

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Run the action while passing the show-password parameter.

```text
juju run fastapi-demo/0 get-db-info show-password=True
```

--------------------------------

### Initialize DatabaseRequires

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Instantiate the DatabaseRequires class within the charm's __init__ method.

```python
# The 'relation_name' comes from the 'charmcraft.yaml file'.
# The 'database_name' is the name of the database that our application requires.
self.database = DatabaseRequires(self, relation_name="database", database_name="names_db")
```

--------------------------------

### Pack the charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Creates a .charm file from the current directory. Use charmcraft clean if packing fails due to stale cache.

```default
charmcraft pack
# Packed fastapi-demo_amd64.charm
```

--------------------------------

### Using the juju fixture

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Demonstrates basic usage of the module-scoped juju fixture for deploying charms and waiting for active status.

```python
# tests/integration/test_charm.py


def test_active(juju: jubilant.Juju, charm_path: pathlib.Path):
    juju.deploy(charm_path)
    juju.wait(jubilant.all_active)

    # Or wait for just 'mycharm' to be active (ignoring other apps):
    juju.wait(lambda status: jubilant.all_active(status, 'mycharm'))
```

--------------------------------

### Configure workload for storage in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Retrieve storage instance paths and update the workload container configuration.

```python
def _update_configuration(self, event: ops.EventBase):
    """Update the workload configuration."""
    cache = self.model.storages['cache']
    if not cache:
        logger.info("No instance available for storage 'cache'.")
        return
    web_cache_path = self.meta.containers['web'].mounts['cache'].location
    # Configure the workload to use the storage instance path (assuming that
    # the workload container image isn't preconfigured to expect storage at
    # the location specified in charmcraft.yaml).
    # For example, provide the storage instance path in the Pebble layer.
    web_container = self.unit.get_container('web')
    try:
        web_container.add_layer(...)
    except ops.pebble.ConnectionError:
        logger.info('Workload container is not available.')
        return
    web_container.replan()
```

--------------------------------

### Define configuration options in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Add configuration definitions under config.options in the charmcraft.yaml file.

```yaml
config:
  options:
    name:
      default: Wiki
      description: The name, or Title of the Wiki
      type: string
    skin:
      default: vector
      description: skin for the Wiki
      type: string
```

--------------------------------

### Launch a Multipass virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Creates a virtual machine named juju-sandbox-k8s with specified resources.

```text
multipass launch --cpus 4 --memory 8G --disk 50G --name juju-sandbox-k8s 24.04
```

--------------------------------

### View directory structure

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

The expected directory structure after creating the new interface.

```default
# tree ./interfaces/my_fancy_database
./interfaces/my_fancy_database
└── v0
    ├── README.md
    ├── interface.yaml
    ├── interface_tests
    └── schema.py
2 directories, 3 files
```

--------------------------------

### Import GrafanaDashboardProvider

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Include the required library import at the top of your src/charm.py file.

```python
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
```

--------------------------------

### Verify library directory structure

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

The expected directory structure after successfully fetching the charm libraries.

```text
lib
└── charms
    └── data_platform_libs
        └── v0
            └── data_interfaces.py
```

--------------------------------

### Test workload container command execution

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Demonstrates how to define expected command outputs and verify execution history using the testing framework.

```python
LS_LL = """
.rw-rw-r--  228 ubuntu ubuntu 18 jan 12:05 -- charmcraft.yaml
.rw-rw-r--  497 ubuntu ubuntu 18 jan 12:05 -- config.yaml
.rw-rw-r--  900 ubuntu ubuntu 18 jan 12:05 -- CONTRIBUTING.md
drwxrwxr-x    - ubuntu ubuntu 18 jan 12:06 -- lib
"""


class MyCharm(ops.CharmBase):
    def _on_start(self, _):
        foo = self.unit.get_container('foo')
        proc = foo.exec(['ls', '-ll'])
        proc.stdin.write('...')
        stdout, _ = proc.wait_output()
        assert stdout == LS_LL


def test_pebble_exec():
    container = testing.Container(
        name='foo',
        execs={
            scenario.Exec(
                command_prefix=['ls'],
                return_code=0,
                stdout=LS_LL,
            ),
        },
    )
    state_in = testing.State(containers={container})
    ctx = testing.Context(
        MyCharm,
        meta={'name': 'foo', 'containers': {'foo': {}}},
    )
    state_out = ctx.run(
        ctx.on.pebble_ready(container),
        state_in,
    )
    assert ctx.exec_history[container.name][0].command == ['ls', '-ll']
    assert ctx.exec_history[container.name][0].stdin == '...'
```

--------------------------------

### Integrate charm with tracing provider

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Use Juju commands to deploy and integrate the charm with a tracing destination like Tempo.

```bash
juju deploy my-charm
juju integrate my-charm tempo
```

--------------------------------

### Prepare application environment variables

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Maps database relation data into a dictionary of environment variables for the application.

```python
def get_app_environment(self) -> dict[str, str]:
    """Return a dictionary of environment variables for the application."""
    db_data = self.fetch_database_relation_data()
    if not db_data:
        return {}
    return {
        "DEMO_SERVER_DB_HOST": db_data["db_host"],
        "DEMO_SERVER_DB_PORT": db_data["db_port"],
        "DEMO_SERVER_DB_USER": db_data["db_username"],
        "DEMO_SERVER_DB_PASSWORD": db_data["db_password"],
    }
```

--------------------------------

### Launch a Multipass virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Creates a virtual machine named juju-sandbox with specified resources.

```text
multipass launch --cpus 4 --memory 8G --disk 50G --name juju-sandbox 24.04
```

--------------------------------

### Mount project directory

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Share the local charm project directory with the virtual machine.

```text
multipass mount --type native /path/to/my-charm juju-sandbox:~/my-charm
multipass shell juju-sandbox
```

--------------------------------

### add_storage

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Creates a new storage device and attaches it to the unit.

```APIDOC
## add_storage(storage_name: str, count: int = 1, *, attach: bool = False)

### Description
Create a new storage device and attach it to this unit.

### Parameters
- **storage_name** (str) - Required - The storage backend name on the Charm.
- **count** (int) - Optional - Number of disks being added.
- **attach** (bool) - Optional - If true, also attach the storage mount.

### Returns
- **list[str]** - A list of storage IDs.
```

--------------------------------

### Introspect the workload container plan

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use get_plan to retrieve the current service configuration and log active services after a replan.

```python
class MyCharm(ops.CharmBase):
    ...

    def _on_config_changed(self, event):
        container = self.unit.get_container('main')
        container.replan()
        plan = container.get_plan()
        for service in plan.services:
            logger.info('Service: %s', service)
        ...
```

--------------------------------

### Inspect Kubernetes resources

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Commands to verify the Juju-created namespace, pod status, and container configuration.

```text
kubectl get namespaces
```

```text
kubectl -n testing get pods
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
modeloperator-5df6588d89-ghxtz   1/1     Running   0          10m
fastapi-demo-0                   2/2     Running   0          10m
```

```text
kubectl -n testing describe pod fastapi-demo-0
```

--------------------------------

### Initialize Kubernetes charm test scaffolding

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Initializes the necessary Spread configuration files for testing a Kubernetes charm within the project directory.

```text
charmcraft init --profile test-kubernetes --force
```

--------------------------------

### Run unit tests

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Commands to execute the unit test suite and view the coverage report.

```text
tox -e unit
```

```text
...

============================================ 12 passed in 0.43s =============================================
unit: commands[1]> coverage report
Name               Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------
src/charm.py          71      5     20      7    87%   71->exit, 101, 106->exit, 115-116, 125-126
src/tinyproxy.py      47     26      6      0    40%   34-41, 52-56, 63, 68, 73-78, 83, 88-90, 95-98, 103-111
--------------------------------------------------------------
TOTAL                118     31     26      7    69%
  unit: OK (1.21=setup[0.05]+cmd[1.03,0.13] seconds)
  congratulations :) (1.30 seconds)
```

--------------------------------

### Implement workload replan

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Define the logic to load configuration, add the Pebble layer, and replan the workload service.

```python
def _replan_workload(self) -> None:
    """Define and start a workload using the Pebble API.

    You'll need to specify the right entrypoint and environment
    configuration for your specific workload. Tip: you can see the
    standard entrypoint of an existing container using docker inspect
    Learn more about interacting with Pebble at
        https://canonical.com/juju/docs/ops/latest/reference/pebble/
    Learn more about Pebble layers at
        https://ubuntu.com/docs/pebble/how-to/use-layers/
    """
    # Learn more about statuses at
    # https://documentation.ubuntu.com/juju/3.6/reference/status/
    self.unit.status = ops.MaintenanceStatus("Assembling Pebble layers")
    try:
        config = self.load_config(FastAPIConfig)
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        self.unit.status = ops.BlockedStatus(str(e))
        return
    try:
        self.container.add_layer(
            "fastapi_demo", self._get_pebble_layer(config.server_port), combine=True
        )
        logger.info("Added updated layer 'fastapi_demo' to Pebble plan")

        # Tell Pebble to incorporate the changes, including restarting the
        # service if required.
        self.container.replan()
        logger.info(f"Replanned with '{self.pebble_service_name}' service")
    except (ops.pebble.APIError, ops.pebble.ConnectionError) as e:
        logger.info("Unable to connect to Pebble: %s", e)
        self.unit.status = ops.MaintenanceStatus("Waiting for Pebble in workload container")
        return
    version = fastapi_demo.get_version(config.server_port)
    self.unit.set_workload_version(version)
    self.unit.status = ops.ActiveStatus()
```

--------------------------------

### Define container and root path

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Initialize the workload container and define the root directory for file operations.

```python
class MyCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.container = self.unit.get_container('myapp')
        self.myapp_root = pathops.ContainerPath(
            '/etc/myapp', container=self.container
        )
        # ...
```

--------------------------------

### run_action(action_name: str, params: dict[str, Any] | None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Simulates running a charm action.

```APIDOC
## run_action(action_name: str, params: dict[str, Any] | None)

### Description
Simulates running a charm action, as with `juju run`.

### Parameters
- **action_name** (str) - Required - The name of the action to run.
- **params** (dict[str, Any]) - Optional - Override the default parameter values found in actions.yaml.

### Raises
- **ActionFailed** - if ops.ActionEvent.fail() is called.
```

--------------------------------

### Define a basic state transition test

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Demonstrates the simplest test scenario with default settings, no configuration, and no leadership.

```python
from ops import testing


def test_basic_scenario():
    ctx = testing.Context(MyCharm)
    state_out = ctx.run(ctx.on.start(), testing.State())
    assert state_out.unit_status == testing.UnknownStatus()
```

--------------------------------

### Handle ExecError for non-zero exit codes

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Demonstrates how to catch and inspect ExecError when a command fails.

```python
>>> process = client.exec(['ls', 'notexist'])
>>> out, err = process.wait_output()
Traceback (most recent call last):
  ...
ExecError: "ls" returned exit code 2
>>> exc = sys.last_value
>>> exc.exit_code
2
>>> exc.stdout
''
>>> exc.stderr
"ls: cannot access 'notfound': No such file or directory\n"
```

--------------------------------

### View Interface Directory Structure

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Displays the expected file layout for a new interface definition.

```text
$ tree ./interfaces/my_fancy_database
./interfaces/my_fancy_database
└── v0
    ├── interface.yaml
    ├── interface_tests
    ├── README.md
    └── schema.py

2 directories, 3 files
```

--------------------------------

### Pack and deploy the charm

Source: https://github.com/canonical/operator/blob/main/README.md

Commands to package the charm and deploy it to a Juju environment.

```shell-script
charmcraft pack
```

```shell-script
juju deploy ./ops-example_ubuntu-22.04-amd64.charm --resource httpbin-image=kennethreitz/httpbin
```

--------------------------------

### Inspect container entrypoint

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Commands to identify the original entrypoint of a container image locally.

```bash
$ docker pull <image>
$ docker inspect <image>
```

--------------------------------

### Access the virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Switches the terminal session to the virtual machine environment.

```text
multipass shell juju-sandbox-k8s
```

--------------------------------

### Import pathops library

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Import the library into your charm code.

```python
from charmlibs import pathops
```

--------------------------------

### Define configuration in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Add the configuration block to charmcraft.yaml to expose the server-port option to users.

```yaml
config:
  options:
    server-port:
      default: 8000
      description: Default port on which FastAPI is available
      type: int
```

--------------------------------

### Run unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Execute the unit test suite for the charm using tox.

```text
tox -e unit
```

--------------------------------

### Configure GitHub Actions for Kubernetes charm integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/set-up-continuous-integration-for-a-charm.md

Add this job to your .github/workflows/ci.yaml file to automate integration testing for Kubernetes charms.

```yaml
  integration:
    name: Integration tests
    runs-on: ubuntu-latest
    needs:
      - unit
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Set up uv
        uses: astral-sh/setup-uv@cec208311dfd045dd5311c1add060b2062131d57  # v8.0.0
      - name: Set up tox and tox-uv
        run: uv tool install tox --with tox-uv
      - name: Set up Concierge
        run: sudo snap install --classic concierge
      - name: Set up Juju and charm development tools
        run: sudo concierge prepare -p k8s
      - name: Pack the charm
        # The integration tests don't pack the charm. Instead, they look for a .charm
        # file in the project dir (or use CHARM_PATH, if set).
        run: charmcraft pack
      - name: Run integration tests
        run: tox -e integration -- --juju-dump-logs logs
      - name: Upload logs
        if: ${{ !cancelled() }}
        uses: actions/upload-artifact@v7
        with:
          name: integration-test-logs
          path: logs
```

--------------------------------

### Create directories

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Create directories within the workload container using ContainerPath.

```python
self.myapp_root.mkdir(parents=True)  # Creates parent directories if needed.
(self.myapp_root / 'private').mkdir(user='myapp', group='myapp')
```

--------------------------------

### Execute test matrix

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Run the test matrix script to verify interface configurations.

```bash
cd path/to/charm-relation-interfaces
python run_matrix.py --include my_fancy_database
```

```bash
cd path/to/my-forked/charm-relation-interfaces
python run_matrix.py --include my_fancy_database --repo https://github.com/your-github-slug/charm-relation-interfaces --branch my-fancy-database
```

--------------------------------

### Test an action using state-transition

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Modern testing approach using the Context API to simulate an action event and verify the output state.

```python
from ops import testing

from charm import DemoCharm


def test_get_value_action():
    ctx = testing.Context(DemoCharm)
    state_in = testing.State()
    ctx.run(ctx.on.action('get-value', params={'value': 'foo'}), state_in)
    assert ctx.action_results == {'out-value': 'foo'}
```

--------------------------------

### Run integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Execute all integration tests defined in the project.

```text
tox -e integration
```

--------------------------------

### Import database interface library

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Import the required database interface classes in src/charm.py.

```python
# Import the 'data_interfaces' library.
# The import statement omits the top-level 'lib' directory
# because 'charmcraft pack' copies its contents to the project root.
from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
)
```

--------------------------------

### Run action events with run()

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Action events are now executed using the standard run() method, with results and logs accessible via the Context object.

```python
# Older Scenario Code
action = Action('backup', params={...})
out = ctx.run_action(action, state)
assert out.logs == ['baz', 'qux']
assert not out.success
assert out.results == {'foo': 'bar'}
assert out.failure == 'boo-hoo'

# Scenario 7.x
with pytest.raises(ActionFailure) as exc_info:
    ctx.run(ctx.on.action('backup', params={...}), State())
assert ctx.action_logs == ['baz', 'qux']
assert ctx.action_results == {'foo': 'bar'}
assert exc_info.value.message == 'boo-hoo'
```

--------------------------------

### push(path: str | PurePath, source: bytes | str | BinaryIO | TextIO, ...)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Writes content to a given file path on the remote system.

```APIDOC
## push(path: str | PurePath, source: bytes | str | BinaryIO | TextIO, *, encoding: str = 'utf-8', make_dirs: bool = False, permissions: int | None = None, user_id: int | None = None, user: str | None = None, group_id: int | None = None, group: str | None = None)

### Description
Write content to a given file path on the remote system.

### Parameters
- **path** (str | PurePath) - Required - Path of the file to write to on the remote system.
- **source** (bytes | str | BinaryIO | TextIO) - Required - Source of data to write.
- **encoding** (str) - Optional - Encoding to use for encoding source str to bytes.
- **make_dirs** (bool) - Optional - If true, create parent directories if they don't exist.
- **permissions** (int) - Optional - Permissions (mode) to create file with.
- **user_id** (int) - Optional - User ID (UID) for file.
- **user** (str) - Optional - Username for file.
- **group_id** (int) - Optional - Group ID (GID) for file.
- **group** (str) - Optional - Group name for file.
```

--------------------------------

### Initialize LogForwarder in charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Instantiate the LogForwarder within the charm's __init__ method to enable log pushing.

```python
# Enable pushing application logs to Loki.
self._logging = LogForwarder(self, relation_name="logging")
```

--------------------------------

### Configure multi-charm packing in tox.ini

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Define a pack environment in tox.ini to build multiple charms using charmcraft.

```ini
[testenv:pack]
commands =
    bash -c "cd charms/foo && charmcraft pack"
    bash -c "cd charms/bar && charmcraft pack"
```

--------------------------------

### Deploy the charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Deploys the packed charm file to the Juju environment.

```text
juju deploy ./tinyproxy_amd64.charm
```

--------------------------------

### Using the juju_factory fixture

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Shows how to manage multiple Juju models within a single test module using the juju_factory fixture.

```python
import jubilant
import pytest
import pytest_jubilant


@pytest.mark.fixture(scope='module')
def other_model(juju_factory: pytest_jubilant.JujuFactory):
    yield juju_factory.get_juju('other')


def test_cross_model(juju: jubilant.Juju, other_model: jubilant.Juju): ...
```

--------------------------------

### Observe the pebble-ready event

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Register an event handler within the charm's __init__ method to respond when the workload container's Pebble is ready.

```python
framework.observe(self.on["demo-server"].pebble_ready, self._on_demo_server_pebble_ready)
```

--------------------------------

### Import Linux operator libraries

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Required import statements for the snap and systemd libraries.

```python
from charms.operator_libs_linux.v0 import systemd
from charms.operator_libs_linux.v1 import snap
```

--------------------------------

### Initialize charm constants and imports

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Required imports and global constants for the charm class.

```python
import time

PORT = 8000
```

--------------------------------

### Deploy PostgreSQL

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Deploy the PostgreSQL charm from the stable channel with trust enabled.

```text
juju deploy postgresql-k8s --channel=14/stable --trust
```

--------------------------------

### View the effective Pebble plan

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Print the merged configuration currently in use by Pebble.

```text
$ /charm/bin/pebble plan
services:
    myworkload:
        summary: my workload service
        startup: enabled
        override: replace
        command: my-workload
```

--------------------------------

### Verify offer creation

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Checks that the observability endpoints are correctly exposed.

```text
juju find-offers cos-lite
```

--------------------------------

### Consuming an application fixture

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Shows how to use the application fixture alongside the juju fixture in a test.

```python
# tests/integration/test_charm.py


def test_active(juju: jubilant.Juju, app: str):
    status = juju.status()
    assert status.apps[app].is_active
```

--------------------------------

### ops.hookcmds.storage_get(id: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves information for a storage instance.

```APIDOC
## ops.hookcmds.storage_get(id: str | None = None)

### Description
Retrieve information for the storage instance with the specified ID.

### Parameters
- **id** (str | None) - Optional - The ID of the storage instance.
```

--------------------------------

### Configure brief logging in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Sets a simple log format for pytest output in the project configuration file.

```toml
[tool.pytest.ini_options]
...
log_cli_format = "%(levelname)s %(name)s %(message)s"
```

--------------------------------

### Verify library directory structure

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

The directory structure after successfully fetching the required libraries.

```text
lib
└── charms
    ├── data_platform_libs
    │   └── v0
    │       └── data_interfaces.py
    ├── grafana_k8s
    │   └── v0
    │       └── grafana_dashboard.py
    ├── loki_k8s
    │   └── v1
    │       └── loki_push_api.py
    ├── observability_libs
    │   └── v0
    │       └── juju_topology.py
    └── prometheus_k8s
        └── v0
            └── prometheus_scrape.py
```

--------------------------------

### Simulate container filesystem with get_filesystem_root

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Use this method to access the temporary directory acting as the container's root filesystem. Tests must manually populate this directory with required files before the charm executes.

```python
# charm.py
class ExampleCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on["mycontainer"].pebble_ready, self._on_pebble_ready)

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        self.hostname = event.workload.pull("/etc/hostname").read()

# test_charm.py
def test_hostname(harness):
    root = harness.get_filesystem_root("mycontainer")
    (root / "etc").mkdir()
    (root / "etc" / "hostname").write_text("hostname.example.com")
    harness.begin_with_initial_hooks()
    assert harness.charm.hostname == "hostname.example.com"
```

--------------------------------

### Navigate to charm repository

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Change directory to the root of the charm operator project.

```text
cd path/to/my-fancy-database-operator
```

--------------------------------

### Implement state-transition tests for the charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Uses ops.testing.Context and ops.testing.State to simulate charm events while mocking the workload module.

```python
# tests/unit/test_charm.py
import pytest
from ops import testing

from charm import MyCharm


class MockWorkload:
    """In-memory stand-in for the workload module."""

    def __init__(self, installed: bool = False, running: bool = False):
        self.installed = installed
        self.running = running
        self.signals: list[str] = []

    def install(self) -> None:
        self.installed = True

    def uninstall(self) -> None:
        self.installed = False

    def is_installed(self) -> bool:
        return self.installed

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def is_running(self) -> bool:
        return self.running

    def reload_config(self) -> None:
        self.signals.append('SIGUSR1')

    def get_version(self) -> str:
        return '1.0.0'


@pytest.fixture
def workload(monkeypatch: pytest.MonkeyPatch) -> MockWorkload:
    mock = MockWorkload()
    monkeypatch.setattr('charm.myworkload', mock)
    return mock


def test_install(workload: MockWorkload):
    # Arrange
    ctx = testing.Context(MyCharm)
    # Act
    state_out = ctx.run(ctx.on.install(), testing.State())
    # Assert
    assert workload.is_installed()
    assert state_out.workload_version == '1.0.0'


def test_start(workload: MockWorkload):
    workload.installed = True
    ctx = testing.Context(MyCharm)
    state_out = ctx.run(ctx.on.start(), testing.State())
    assert workload.is_running()
    assert state_out.unit_status == testing.ActiveStatus()


def test_stop(workload: MockWorkload):
    workload.installed = True
    workload.running = True
    ctx = testing.Context(MyCharm)
    ctx.run(ctx.on.stop(), testing.State())
    assert not workload.is_running()
```

--------------------------------

### Execute process with string input/output

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use wait_output to receive standard output and error as strings. Input is provided via the stdin parameter.

```python
process = container.exec(['tr', 'a-z', 'A-Z'], stdin='This is\na test\n')
stdout, _ = process.wait_output()
logger.info('Output: %r', stdout)
```

--------------------------------

### Mount files for container interaction

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use mounts to provide files to the container or capture data written by the charm during event handling.

```python
def test_get_backup_action(tmp_path):
    # Create a temporary file with placeholder data, then mount the file
    # in the workload container so that our charm can see it.
    backup_file = tmp_path / 'backup.yaml'
    backup_file.write_text(my_custom_data())
    ctx = testing.Context(MyCharm)
    container = testing.Container(
        'myapp',
        can_connect=True,
        mounts={
            'backup': testing.Mount(
                location='/etc/myapp/backup.yaml', source=backup_file
            )
        },
    )
    state_in = testing.State(containers={container})
    state_out = ctx.run(ctx.on.action('get-backup'), state_in)

    # Check that the action returned the contents of backup_file.
    assert ctx.action_results == {'data': my_custom_data()}
```

--------------------------------

### Creating an application fixture

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Defines a module-scoped fixture to handle complex application deployment and configuration.

```python
# tests/integration/conftest.py
import pathlib

import jubilant
import pytest


@pytest.fixture(scope='module')
def app(juju: jubilant.Juju, charm_path: pathlib.Path):
    my_app_name = 'mycharm'
    juju.deploy(
        charm_path,
        my_app_name,
        resources={
            'mycharm-image': 'ghcr.io/canonical/...',
        },
        config={
            'base_url': '/api',
            'port': 80,
        },
        base='ubuntu@20.04',
    )
    # ... do any other application setup here ...
    juju.wait(jubilant.all_active)
    yield my_app_name
```

--------------------------------

### Verify the effective Pebble plan

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Use this command to inspect the merged configuration plan currently active in Pebble.

```text
$ pebble plan
services:
    myapp:
        summary: my application
        startup: enabled
        override: replace
        command: /bin/myapp --port 8080
```

--------------------------------

### container_pebble_ready(container_name: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Simulates the pebble_ready hook for a specific container.

```APIDOC
## container_pebble_ready(container_name: str)

### Description
Fire the pebble_ready hook for the associated container. This will switch the given container’s can_connect state to True before the hook function is called.

### Parameters
- **container_name** (str) - Required - The name of the container to trigger the hook for.
```

--------------------------------

### Unit test for action with parameters

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Test the get_db_info action when show-password is set to True.

```python
def test_get_db_info_action_show_password():
    ctx = testing.Context(FastAPIDemoCharm)
    relation = testing.Relation(
        endpoint="database",
        interface="postgresql_client",
        remote_app_name="postgresql-k8s",
        remote_app_data={
            "endpoints": "example.com:5432",
            "username": "foo",
            "password": "bar",
        },
    )
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        relations={relation},
        leader=True,
    )

    ctx.run(ctx.on.action("get-db-info", params={"show-password": True}), state_in)

    assert ctx.action_results == {
        "db-host": "example.com",
        "db-port": "5432",
        "db-username": "foo",
        "db-password": "bar",
    }
```

--------------------------------

### Update workload configuration with overlay layers

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Demonstrates using a config-changed callback to merge new environment variables into the existing Pebble layer and replan the workload.

```python
# ...
import ops
# ...
def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
    """Handle the config changed event."""
    # Get a reference to the container so we can manipulate it
    container = self.unit.get_container(self.name)

    # Create a new config layer - specify 'override: merge' in
    # the 'pause' service definition to overlay with existing layer
    layer = ops.pebble.Layer(
        {
            "services": {
                "pause": {
                    "override": "merge",
                    "environment": {
                        "TIMEOUT": self.config["timeout"],
                    },
                }
            },
        }
    )

    try:
        # Add the layer to Pebble
        container.add_layer(self.name, layer, combine=True)
        logging.debug("Added config layer to Pebble plan")

        # Tell Pebble to update the plan, which will restart any services if needed.
        container.replan()
        logging.info("Updated pause service")
        # All is well, set an ActiveStatus
        self.unit.status = ops.ActiveStatus()
    except ops.pebble.PathError, ops.pebble.ProtocolError, ops.pebble.ConnectionError:
        # handle errors (for example: the container might not be ready yet)
        .....
```

--------------------------------

### list_files(path: str | PurePath, *, pattern: str | None = None, itself: bool = False) -> list[FileInfo]

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Return list of directory entries from given path on remote system.

```APIDOC
## list_files

### Description
Return list of directory entries from given path on remote system. Returns a list of files and directories.

### Parameters
- **path** (str | PurePath) - Required - Path of the directory to list, or path of the file to return information about.
- **pattern** (str) - Optional - If specified, filter the list to just the files that match.
- **itself** (bool) - Optional - If path refers to a directory, return information about the directory itself.
```

--------------------------------

### Initialize container attributes

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Define the workload container and service name attributes in the charm's __init__ method.

```python
# See 'containers' in charmcraft.yaml.
self.container = self.unit.get_container("demo-server")
self.pebble_service_name = "fastapi"
```

--------------------------------

### Inspect container filesystem in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use get_filesystem to retrieve a temporary directory simulating the container's filesystem for verification.

```python
def test_pebble_ready():
    ctx = testing.Context(MyCharm)
    container = testing.Container('myapp', can_connect=True)
    state_in = testing.State(containers={container})
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)

    # Check that the workload container has the expected config file
    # after our charm handles the pebble-ready event.
    container_root = state_out.get_container('myapp').get_filesystem(ctx)
    config_file = container_root / 'etc' / 'myapp' / 'config.yaml'
    assert config_file.exists()
    assert my_custom_checks(config_file)
```

--------------------------------

### Draft a release using tox

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Commands to initiate the release drafting process with various configuration parameters.

```bash
tox -e draft-release
```

```bash
tox -e draft-release -- --canonical-remote origin --fork-remote mine
```

```bash
tox -e draft-release -- --branch 2.23-maintenance
```

--------------------------------

### Inspect state with custom scripts

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Run Python scripts on a live unit to inspect charm state directly.

```python
# inspect_relations.py
def main(charm):
    for relation in charm.model.relations['database']:
        print(relation.data[relation.app])
```

```shell
jhack script myapp/0 ./inspect_relations.py
```

--------------------------------

### Generate and test charms from templates

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Use this script to verify Charmcraft profile templates by generating new projects and running lint and unit tests.

```bash
#!/usr/bin/env bash
set -xueo pipefail

charmcraft_dir="$1"

for profile in kubernetes machine; do
    project="myapp-${profile}"
    rm -rf "${project}"
    uv run --project "$charmcraft_dir" --no-dev \
        charmcraft init --profile "${profile}" --project-dir "${project}"
    pushd "${project}"
    uv lock
    uvx --python 3.10 --with tox-uv tox -e lint,unit
    popd
done
```

--------------------------------

### Deploy COS Lite bundle

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Creates a dedicated model for observability and deploys the COS Lite bundle.

```text
juju add-model cos-lite
juju deploy cos-lite --trust
```

--------------------------------

### Run Pebble Integration Tests

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Execute tests that require a live Pebble server instance.

```sh
tox -e pebble
```

--------------------------------

### handle_exec(container, command_prefix, *, handler=None, result=None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Registers a handler to simulate Pebble command execution within a container.

```APIDOC
## handle_exec

### Description
Register a handler to simulate the Pebble command execution. This allows a test harness to simulate the behavior of running commands in a container.

### Parameters
- **container** (str | Container) - Required - The specified container or its name.
- **command_prefix** (Sequence[str]) - Required - The command prefix to register against.
- **handler** (Callable[[ExecArgs], ExecResult | None]) - Optional - A handler function that simulates the command’s execution.
- **result** (int | str | bytes | ExecResult) - Optional - A simplified form to specify the command’s simulated result.
```

--------------------------------

### Deploy the charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Deploys the local charm file to the Kubernetes cluster, specifying the required resource image.

```text
juju deploy ./fastapi-demo_amd64.charm --resource \
     demo-server-image=ghcr.io/canonical/api_demo_server/api-demo-server:2.1.0
```

--------------------------------

### Define resources using Resource class

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Resources are now defined as scenario.Resource objects rather than plain dictionaries.

```python
# Older Scenario code
state = State(resources={'/path/to/foo', pathlib.Path('/mock/foo')})

# Scenario 7.x
resource = Resource(location='/path/to/foo', source=pathlib.Path('/mock/foo'))
state = State(resources={resource})
```

--------------------------------

### Configure GitHub Actions for integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/set-up-continuous-integration-for-a-charm.md

A minimal GitHub Actions workflow configuration to run integration tests using charmcraft and Spread.

```yaml
  integration:
    name: Integration / ${{ matrix.task }}
    runs-on: ubuntu-latest
    needs:
      - unit
    strategy:
      fail-fast: false
      matrix:
        task:
          - test_charm
          # Add one entry per spread/integration/<module>/task.yaml.
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - name: Set up LXD
        uses: canonical/setup-lxd@8c6a87bfb56aa48f3fb9b830baa18562d8bfd4ee  # v1
        with:
          channel: 5.21/stable
      - name: Install charmcraft
        run: sudo snap install charmcraft --classic
      - name: Run spread test
        # On GitHub Actions (CI=true) charmcraft test runs spread against the
        # runner itself, instead of launching a nested LXD VM.
        run: charmcraft test "craft:ubuntu-24.04:spread/integration/${{ matrix.task }}"
```

--------------------------------

### Test configuration change

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Verify that the charm correctly applies the server-port configuration to the Pebble service command.

```python
def test_config_changed(mock_version):
    ctx = testing.Context(FastAPIDemoCharm)
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        config={"server-port": 8080},
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    command = state_out.get_container(container.name).plan.services["fastapi"].command
    assert "--port 8080" in command
```

--------------------------------

### Implement a basic reconciler method

Source: https://github.com/canonical/operator/blob/main/docs/explanation/holistic-vs-delta-charms.md

Demonstrates the core logic of a reconciler: reading inputs, computing the new state, and updating the workload or relations if changes are detected.

```python
# Read the inputs
path = self.typed_config.some_path
foo_value = self.foo_requirer.some_relation_property
bar_value = self.bar_provider.some_relation_property
current_config = self.workload.config

# Compute the new state
workload_config = self.render_config(path, foo_value, bar_value)

# Write the outputs
if workload_config != current_config:
    self.workload.update_config_and_restart(workload_config)
self.foo_requirer.update_some_relation_field(bar_value)
self.bar_provider.update_some_relation_field(foo_value)
```

--------------------------------

### Configure interface.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Define the provider charm metadata in the interface configuration file.

```yaml
# interface.yaml
providers:
  - name: my-fancy-database-operator  # same as metadata.yaml's .name
    url: https://github.com/your-github-slug/my-fancy-database-operator
```

--------------------------------

### Automate version file creation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-charm-version.md

Use an override-build step in charmcraft.yaml to automatically generate the version file during the build process.

```yaml
parts:
  charm:
    source: .
    plugin: uv
    build-packages: [git]
    build-snaps: [astral-uv]
    override-build: |
      craftctl default  # Run the default build steps.
      git describe --always > $CRAFT_PART_INSTALL/version
```

--------------------------------

### Check directory existence

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Verify if a directory exists and confirm it is a directory.

```python
(self.myapp_root / 'cachedir').exists()
(self.myapp_root / 'cachedir').is_dir()
```

--------------------------------

### Load typed configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Initialize the typed configuration within the charm's __init__ method using load_config.

```python
self.typed_config = self.load_config(WikiConfig, errors='blocked')
```

--------------------------------

### Define storage in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Configure storage and container mounts for a Kubernetes charm.

```yaml
storage:
  cache:
    description: Somewhere to cache files locally.
    type: filesystem
    properties:
      - transient
    minimum-size: 1G

containers:
  web:
    resource: web-image
    mounts:
      - storage: cache
        location: /var/cache
```

--------------------------------

### Call the workload module from charm.py

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Demonstrates how to integrate a separate workload module into the main charm class by observing lifecycle events.

```python
import ops
import myworkload


class MyCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.start, self._on_start)
        framework.observe(self.on.stop, self._on_stop)
        framework.observe(self.on.remove, self._on_remove)
        framework.observe(self.on.collect_unit_status, self._on_collect_status)

    def _on_install(self, event: ops.InstallEvent) -> None:
        if not myworkload.is_installed():
            myworkload.install()
            self.unit.set_workload_version(myworkload.get_version())

    def _on_start(self, event: ops.StartEvent) -> None:
        myworkload.start()

    def _on_stop(self, event: ops.StopEvent) -> None:
        myworkload.stop()

    def _on_remove(self, event: ops.RemoveEvent) -> None:
        # On shared machines, avoid automatically uninstalling system packages.
        # Stop the workload here, and only remove packages as an explicit,
        # charm-specific step when you know the machine is dedicated to it.
        myworkload.stop()

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        if not myworkload.is_installed():
            event.add_status(ops.MaintenanceStatus('Installing workload'))
        if not myworkload.is_running():
            event.add_status(ops.MaintenanceStatus('Starting workload'))
        event.add_status(ops.ActiveStatus())
```

--------------------------------

### Implement charm status transitions

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Demonstrates setting various unit statuses within a charm event handler to reflect processing stages.

```python
# charm code:
def _on_event(self, _event):
    self.unit.status = ops.MaintenanceStatus('determining who the ruler is...')
    try:
        if self._call_that_takes_a_few_seconds_and_only_passes_on_leadership():
            self.unit.status = ops.ActiveStatus('I rule')
        else:
            self.unit.status = ops.WaitingStatus('checking this is right...')
            self._check_that_takes_some_more_time()
            self.unit.status = ops.ActiveStatus('I am ruled')
    except:
        self.unit.status = ops.BlockedStatus('something went wrong')
```

--------------------------------

### Add logging to the charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Import the logging module and initialize a logger to enable debug-log output in Juju.

```python
import logging

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)
```

--------------------------------

### Define Workload-Specific Logic

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Functions for managing the Demo Server workload, located in src/demo_server.py.

```python
# Copyright 2025 User
# See LICENSE file for licensing details.

"""Functions for managing and interacting with the server."""

import logging
import subprocess

import requests

logger = logging.getLogger(__name__)


def install() -> None:
    """Install the server from a snap."""
    subprocess.run(
        ['snap', 'install', 'demo-server'], capture_output=True, check=True
    )


def start() -> None:
    """Start the server."""
    subprocess.run(['demo-server', 'start'], capture_output=True, check=True)


def get_version() -> str:
    """Get the running version of the server."""
    response = requests.get('http://localhost:5000/version', timeout=5)
    return response.text
```

--------------------------------

### Analyze charm directory structure

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Displays the file layout of a legacy hooks-based charm.

```text
$ tree .
.
├── charmcraft.yaml
├── config.yaml
├── copyright
├── hooks
│   ├── config-changed
│   ├── install
│   ├── start
│   ├── stop
│   ├── update-status
│   ├── upgrade-charm
│   ├── website-relation-broken
│   ├── website-relation-changed
│   ├── website-relation-departed
│   └── website-relation-joined
├── icon.svg
├── LICENSE
├── metadata.yaml
├── microsample-ha.png
├── README.md
└── revision
```

--------------------------------

### Simulate user secret management

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Demonstrates adding a user secret and configuring a charm to access it during testing.

```default
# charmcraft.yaml
config:
  options:
    mysec:
      type: secret
      description: "tell me your secrets"

# charm.py
class MyVMCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        mysec = self.config.get('mysec')
        if mysec:
            sec = self.model.get_secret(id=mysec, label="mysec")
            self.config_from_secret = sec.get_content()

# test_charm.py
def test_config_changed(harness):
    secret_content = {'password': 'foo'}
    secret_id = harness.add_user_secret(secret_content)
    harness.grant_secret(secret_id, 'test-charm')
    harness.begin()
    harness.update_config({'mysec': secret_id})
    secret = harness.model.get_secret(id=secret_id).get_content()
    assert harness.charm.config_from_secret == secret.get_content()
```

--------------------------------

### Configure charm metadata

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Update the charmcraft.yaml file with descriptive metadata for the charm.

```yaml
title: Web Server Demo
summary: A demo charm that operates a small Python FastAPI server.
description: |
  This charm demonstrates how to write a Kubernetes charm with Ops.
```

--------------------------------

### Instantiate Tracing in the charm class

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Initialize the Tracing object within the charm's __init__ method to enable automatic event and API tracing.

```python
class MyCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.tracing = ops.tracing.Tracing(
            self,
            tracing_relation_name='charm-tracing',
            ca_relation_name='receive-ca-cert',
        )
        ...
```

--------------------------------

### Check file existence

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Verify if a file exists and confirm it is a file.

```python
(self.myapp_root / 'backup.yaml').exists()
(self.myapp_root / 'backup.yaml').is_file()
```

--------------------------------

### Migrate Charm Deployment

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Replace asynchronous deployment and idle waiting with synchronous Juju commands and ready callables.

```python
# pytest-operator
postgres_app = await model.deploy(
    'postgresql-k8s',
    channel='14/stable',
    series='jammy',
    revision=300,
    trust=True,
    config={'profile': 'testing'},
)
await model.wait_for_idle(apps=[postgres_app.name], status='active')

# jubilant
juju.deploy(
    'postgresql-k8s',
    channel='14/stable',
    base='ubuntu@22.04',
    revision=300,
    trust=True,
    config={'profile': 'testing'},
)
juju.wait(lambda status: jubilant.all_active(status, 'postgresql-k8s'))
```

--------------------------------

### Reset configuration and verify status

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Revert the port configuration and check that the application returns to an active state.

```text
juju config fastapi-demo server-port=8000
juju status
```

--------------------------------

### Specify events via context.on

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Use the unified ctx.on.{event name}() syntax for triggering events instead of passing strings or explicit Event objects.

```python
# Older Scenario code.
ctx.run('start', state)
ctx.run(container.pebble_ready_event, state)
ctx.run(Event('relation-joined', relation=relation), state)

# Scenario 7.x
ctx.run(ctx.on.start(), state)
ctx.run(ctx.on.pebble_ready(container=container), state)
ctx.run(ctx.on.relation_joined(relation=relation), state)
```

```python
# Older Scenario code.
action = Action('backup', params={...})
ctx.run_action(action, state)

# Scenario 7.x
ctx.run(ctx.on.action('backup', params={...}), state)
```

--------------------------------

### Request storage instances via CLI

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use the Juju CLI to request additional storage instances for a specific unit.

```text
juju add-storage <unit> cache=2  # Request two more instances.
```

--------------------------------

### Implement action event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Define the logic for the action, including parameter loading, logging, failure reporting, and result setting.

```python
def _on_snapshot_action(self, event: ops.ActionEvent):
    """Handle the snapshot action."""
    # Fetch the parameters. If the user passes something invalid, this will
    # fail the action with an appropriate message.
    params = event.load_params(SnapshotAction, errors='fail')
    # This might take a while, so let the user know we're working on it.
    # This is sent back to the Juju user in real-time, and appears in the output
    # of the `juju run` command.
    event.log(f'Generating snapshot into {params.filename}')
    # Do the snapshot. This returns the size of the snapshot in bytes.
    size = self.do_snapshot(
        filename=params.filename,
        kind=params.compression.kind,
        quality=params.compression.quality,
    )
    if size is None:
        # Report to the user that the action has failed.
        event.fail(
            'Failed to generate snapshot.'
        )  # Ideally, include more details than this!
        # Note that `fail()` doesn't interrupt code, so is typically followed by a `return`.
        return
    # Set the results of the action. These will be displayed in the
    # `juju run` output.
    event.set_results({'snapshot-size': str(size)})
```

--------------------------------

### Implement stop and remove event handlers

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Define the methods to handle service termination and uninstallation, including a helper to verify the service has stopped.

```python
    def _on_stop(self, event: ops.StopEvent) -> None:
        """Handle stop event."""
        tinyproxy.stop()
        self.wait_for_not_running()

    def _on_remove(self, event: ops.RemoveEvent) -> None:
        """Handle remove event."""
        tinyproxy.uninstall()

    def wait_for_not_running(self) -> None:
        """Wait for tinyproxy to not be running."""
        for _ in range(3):
            if not tinyproxy.is_running():
                return
            time.sleep(1)
        raise RuntimeError("tinyproxy was still running after the expected time")
```

--------------------------------

### Import LogForwarder library

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Import the LogForwarder class from the loki_push_api library in your charm.py file.

```python
from charms.loki_k8s.v1.loki_push_api import LogForwarder
```

--------------------------------

### Test pebble-ready event

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Unit test verifying that the pebble-ready event correctly writes a file to the container filesystem.

```python
import yaml
from ops import testing

from charm import MyCharm


def test_pebble_ready_writes_config_file():
    """Test that on pebble-ready, a config file is written."""
    # Arrange: setting up the inputs
    ctx = testing.Context(MyCharm)
    container = testing.Container(name='some-container', can_connect=True)
    state_in = testing.State(
        containers=[container],
        leader=True,
    )

    # Act:
    state_out = ctx.run(ctx.on.pebble_ready(container=container), state_in)

    # Assert:
    container_fs = state_out.get_container('some-container').get_filesystem(ctx)
    cfg_file = container_fs / 'etc' / 'config.yaml'
    config = yaml.safe_load(cfg_file.read_text())
    assert config['message'] == 'Hello, world!'
```

--------------------------------

### Run post-release tasks

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Executes the post-release automation script after a successful release.

```bash
tox -e post-release
```

--------------------------------

### ops.hookcmds.config_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieve application configuration settings.

```APIDOC
## ops.hookcmds.config_get(key: str | None = None)

### Description
Retrieve application configuration. If called without arguments, returns a dictionary containing all config settings. If called with a key, it returns the value of that specific config option.

### Parameters
- **key** (str) - Optional - The configuration option to retrieve.
```

--------------------------------

### Execute a command and capture output

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Executes a command and retrieves stdout and stderr as strings using wait_output.

```python
>>> process = client.exec(['python3', '--version'])
>>> version, _ = process.wait_output()
>>> print(version)
Python 3.8.10
```

```python
>>> process = client.exec(['pg_dump', '-s', ...])
>>> schema, logs = process.wait_output()
```

--------------------------------

### Enter the container as root using nsenter

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Use nsenter from the host node to enter the container as root, bypassing Pebble for deep inspection.

```shell
# On the node:
apt install busybox-static
cp /usr/bin/busybox /proc/<pebble-pid>/root/charm/bin/busybox
nsenter -a -t <pebble-pid> -S 0 -G 0 /charm/bin/busybox sh
# whoami
root
```

--------------------------------

### ops.hookcmds.storage_list(name: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Lists storage attached to the unit.

```APIDOC
## ops.hookcmds.storage_list(name: str | None = None)

### Description
List storage attached to the unit.

### Parameters
- **name** (str | None) - Optional - Only list storage with this name.
```

--------------------------------

### Replace convenience methods with dataclasses.replace

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Replace deprecated with_* convenience methods on the State class with the standard dataclasses.replace mechanism.

```python
# Older Scenario code
new_state = state.with_can_connect(container_name, can_connect=True)
new_state = state.with_leadership(leader=True)
new_state = state.with_unit_status(status=ActiveStatus())

# Scenario 7.x
new_container = dataclasses.replace(container, can_connect=True)
new_state = dataclasses.replace(containers={container})
new_state = dataclasses.replace(state, leader=True)
new_state = dataclasses.replace(state, status=ActiveStatus())
```

--------------------------------

### Test an action using Harness

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Legacy testing approach using the Harness class to instantiate the charm and run actions.

```python
from ops import testing

from charm import DemoCharm


def test_action():
    harness = testing.Harness(DemoCharm)
    harness.begin()
    output = harness.run_action('get-value', {'value': 'foo'})
    assert output.results == {'out-value': 'foo'}
    harness.cleanup()
```

--------------------------------

### Provide return type annotations

Source: https://github.com/canonical/operator/blob/main/STYLE.md

Include return type annotations for all functions and methods, excluding __init__ and test code.

```python
def method1(arg1: type1, arg2: type2) -> None:
    return


def method2() -> str:
    ...
    return 'Hello world!'


class C:
    def __init__(self, x: type1):
        pass


def test_method1():
    assert ...
```

--------------------------------

### Record a custom notice via CLI

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-custom-notices.md

Use the pebble notify command to record a notice with a specific key and optional data arguments.

```sh
pg_dump mydb >/tmp/mydb.sql
/charm/bin/pebble notify canonical.com/postgresql/backup-done path=/tmp/mydb.sql
```

--------------------------------

### Define container state for testing

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Initialize a testing state with specific containers and their connection status.

```python
state = testing.State(
    containers={
        testing.Container(name='foo', can_connect=True),
        testing.Container(name='bar', can_connect=False),
    }
)
```

--------------------------------

### Interact with the workload

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Shows how to retrieve application status and connect to a workload address.

```python
def test_workload_connectivity(charm: pathlib.Path, juju: jubilant.Juju):
    status = juju.status()
    app_address = status.applications['my_app'].address
    # Or you can try to connect to a concrete unit
    # address = status.apps[
```

--------------------------------

### Test helper module version retrieval

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Demonstrates mocking subprocess calls to verify the helper module's version detection logic.

```python
import pytest

from charm import tinyproxy


class MockVersionProcess:
    """Mock object that represents the result of calling 'tinyproxy -v'."""

    def __init__(self, version: str):
        self.stdout = f"tinyproxy {version}"


def test_version(monkeypatch: pytest.MonkeyPatch):
    """Test that the helper module correctly returns the version of tinyproxy."""
    version_process = MockVersionProcess("1.0.0")
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: version_process)
    assert tinyproxy.get_version() == "1.0.0"
```

--------------------------------

### Test a charm using a library

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Use the testing context to simulate custom events emitted by a library.

```python
from ops import testing
from charms.charm_with_lib.v0.database_lib import DatabaseRequirer


def test_ready_event():
    ctx = testing.Context(MyCharm)
    secret = testing.Secret({'username': 'admin', 'password': 'admin'})
    state_in = testing.State(secrets={secret})

    state_out = ctx.run(
        ctx.on.custom(DatabaseRequirer, credential_secret=secret), state_in
    )

    assert ...
```

--------------------------------

### ops.hookcmds.storage_add(counts: Mapping[str, int])

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Adds storage instances.

```APIDOC
## ops.hookcmds.storage_add(counts: Mapping[str, int])

### Description
Add storage instances.

### Parameters
- **counts** (Mapping[str, int]) - Required - A map of storage names to the number of instances of that storage to create.
```

--------------------------------

### Configure tox for integration tests

Source: https://github.com/canonical/operator/blob/main/docs/explanation/testing.md

Set the base Python version in tox to match the OS specified in charmcraft.yaml.

```ini
[testenv]
basepython = python3.10
```

--------------------------------

### Define configuration in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Configures the 'slug' option in the charmcraft.yaml file to inform Juju and Ops.

```yaml
config:
  options:
    slug:
      description: "Configures the path of the reverse proxy. Must match the regex [a-z0-9-]+"
      default: example
      type: string
```

--------------------------------

### Verify charm storage state with Context

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use the Context object to mock filesystem storage and verify file operations within a charm's event lifecycle.

```python
from ops import testing

# Some charm with a 'foo' filesystem-type storage defined in its metadata:
ctx = testing.Context(MyCharm)
storage = testing.Storage('foo')

# Set up storage with some content:
(storage.get_filesystem(ctx) / 'myfile.txt').write_text('helloworld')

with ctx(ctx.on.update_status(), testing.State(storages={storage})) as mgr:
    foo = mgr.charm.model.storages['foo'][0]
    loc = foo.location
    path = loc / 'myfile.txt'
    assert path.exists()
    assert path.read_text() == 'helloworld'

    myfile = loc / 'path.py'
    myfile.write_text('helloworlds')

    state_out = mgr.run()

# Verify that the contents are as expected afterwards.
assert (
    state_out.get_storage(storage.name).get_filesystem(ctx) / 'path.py'
).read_text() == 'helloworlds'
```

--------------------------------

### populate_oci_resources()

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Populate all OCI resources.

```APIDOC
## populate_oci_resources

### Description
Populate all OCI resources.
```

--------------------------------

### Implement workload version helper

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Create a helper module to fetch the workload version from the application's /version endpoint.

```python
import json
import logging
import urllib.request

logger = logging.getLogger(__name__)


def get_version(port: int) -> str:
    """Get the version of fastapi_demo that is running.

    Args:
        port: The port where fastapi_demo web server is listening.
    """
    response = urllib.request.urlopen(f"http://localhost:{port}/version")
    data = json.loads(response.read())
    return data["version"]
```

--------------------------------

### Access Juju environment

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Commands to enter the sandbox and monitor deployment status.

```text
multipass shell juju-sandbox
```

```text
juju status --watch 2s
```

--------------------------------

### Execute process with file-like objects

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Pass file-like objects to stdin, stdout, and stderr parameters and use wait() instead of wait_output().

```python
with open('LICENSE.txt') as stdin:
    with open('output.txt', 'w') as stdout:
        process = container.exec(
            ['tr', 'a-z', 'A-Z'],
            stdin=stdin,
            stdout=stdout,
            stderr=sys.stderr,
        )
        process.wait()
```

--------------------------------

### Client.exec(command, ...)

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Executes a command within the Pebble environment. Allows configuration of environment variables, working directory, user/group context, and stream handling for stdin, stdout, and stderr.

```APIDOC
## Client.exec(command, ...)

### Description
Executes a command in the Pebble environment. Returns a Process object representing the running process.

### Parameters
- **command** (list) - Required - The command to execute (executable name/path and arguments).
- **service_context** (str) - Optional - Run command in the context of a specific service.
- **environment** (dict) - Optional - Environment variables to pass to the process.
- **working_dir** (str) - Optional - Working directory for the command.
- **timeout** (int) - Optional - Timeout in seconds.
- **user** (str) - Optional - Username to run as.
- **group** (str) - Optional - Group name to run as.
- **stdin** (str/file-like) - Optional - Input for the process.
- **stdout** (file-like) - Optional - Destination for standard output.
- **stderr** (file-like) - Optional - Destination for standard error.
- **combine_stderr** (bool) - Optional - Combine stderr into stdout.

### Returns
- **Process** - An object representing the state of the running process.

### Raises
- **APIError** - If communication fails or command is not found.
- **ExecError** - If the command exits with a non-zero code.
```

--------------------------------

### push_path(source_path, dest_dir)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Recursively push a local path or files to the remote system.

```APIDOC
## push_path(source_path: str | Path | Iterable[str | Path], dest_dir: str | PurePath)

### Description
Recursively push a local path or files to the remote system. Only regular files and directories are copied; symbolic links and device files are skipped.

### Parameters
- **source_path** (str | Path | Iterable[str | Path]) - Required - A single path or list of paths to push to the remote system.
- **dest_dir** (str | PurePath) - Required - Remote destination directory inside which the source dir/files will be placed.
```

--------------------------------

### Define a configuration dataclass

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Create a dataclass to represent charm configuration with validation logic in the __post_init__ method.

```python
@dataclasses.dataclass(frozen=True, kw_only=True)
class FastAPIConfig:
    """Configuration for the FastAPI demo charm."""

    server_port: int = 8000
    """Default port on which FastAPI is available."""

    def __post_init__(self):
        """Validate the configuration."""
        if self.server_port == 22:
            raise ValueError("Invalid port number, 22 is reserved for SSH")
```

--------------------------------

### Exit virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Closes the shell session and returns to the host machine.

```text
exit
```

--------------------------------

### Construct Pebble layer

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Create a method to generate a Pebble layer that merges service definitions with custom port configurations.

```python
def _get_pebble_layer(self, port: int) -> ops.pebble.Layer:
    """Pebble layer for the FastAPI demo services."""
    cmd = f"/bin/uvicorn api_demo_server.app:app --host 0.0.0.0 --port {port}"
    service: ops.pebble.ServiceDict = {
        "override": "merge",
        "command": cmd,
    }
    layer: ops.pebble.LayerDict = {
        "summary": "FastAPI demo service",
        "description": "pebble config layer for FastAPI demo server",
        "services": {self.pebble_service_name: service},
    }
    return ops.pebble.Layer(layer)
```

--------------------------------

### Define an action in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Add an actions block to your charmcraft.yaml file to define the get-db-info action and its parameters.

```yaml
actions:
  get-db-info:
    description: Fetches database authentication information
    params:
      show-password:
        description: Show username and password in output information
        type: boolean
        default: false
    additionalProperties: false
```

--------------------------------

### Define a charm class with container management

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

A sample charm class that manages a container, observes pebble-ready events, and reports unit status.

```python
class DemoCharm(ops.CharmBase):
    """Manage the workload."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self.container = self.unit.get_container('my-container')
        framework.observe(
            self.on['my-container'].pebble_ready, self._on_pebble_ready
        )
        framework.observe(self.on.collect_unit_status, self._on_collect_status)

    def _on_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        """Use Pebble to configure and start the workload in the container."""
        layer: ops.pebble.LayerDict = {
            'services': {
                'workload': {
                    'override': 'replace',
                    'command': 'run-workload',
                    'startup': 'enabled',
                }
            }
        }
        self.container.add_layer('base', layer, combine=True)
        self.container.replan()
        ...  # Check that the workload is actually running.

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        """Report the status of the workload."""
        try:
            service = self.container.get_service('workload')
        except (ops.ModelError, ops.pebble.ConnectionError):
            event.add_status(ops.MaintenanceStatus('waiting for container'))
        else:
            if not service.is_running():
                event.add_status(ops.MaintenanceStatus('waiting for workload'))
        event.add_status(ops.ActiveStatus())
```

--------------------------------

### Run a charm action with validation

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Shows how to validate action parameters against the charm's metadata schema using jsonschema before executing the action.

```default
schema = harness.charm.meta.actions["action-name"].parameters
try:
    jsonschema.validate(instance=params, schema=schema)
except jsonschema.ValidationError:
    # Do something about the invalid params.
    ...
harness.run_action("action-name", params)
```

--------------------------------

### Execute simulation script

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Commands to enter the environment and run the traffic simulation script.

```text
multipass shell juju-sandbox-k8s
```

```text
chmod +x ~/fastapi-demo/simulate.sh
. ~/fastapi-demo/simulate.sh
```

--------------------------------

### View charm database file permissions

Source: https://github.com/canonical/operator/blob/main/docs/explanation/security.md

Displays the file permissions for the state and tracing databases located in the charm directory.

```text
-rw-r--r--  1 root root  32K Jul 13 23:48 .tracing-data.db
-rw-------  1 root root  20K Jul 13 23:48 .unit-state.db
```

--------------------------------

### Unit test for action

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Test the default behavior of the get_db_info action.

```python
def test_get_db_info_action():
    ctx = testing.Context(FastAPIDemoCharm)
    relation = testing.Relation(
        endpoint="database",
        interface="postgresql_client",
        remote_app_name="postgresql-k8s",
        remote_app_data={
            "endpoints": "example.com:5432",
            "username": "foo",
            "password": "bar",
        },
    )
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        relations={relation},
        leader=True,
    )

    ctx.run(ctx.on.action("get-db-info", params={"show-password": False}), state_in)

    assert ctx.action_results == {
        "db-host": "example.com",
        "db-port": "5432",
    }
```

--------------------------------

### Define container and resource configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Specify the OCI image resource and container mapping in charmcraft.yaml.

```yaml
containers:
  demo-server:
    resource: demo-server-image

resources:
  # An OCI image resource for the container listed above.
  demo-server-image:
    type: oci-image
    description: OCI image from GitHub Container registry
    # The upstream-source field is ignored by Charmcraft and Juju, but it can be
    # useful to developers in identifying the source of the OCI image.  It is also
    # used by the 'canonical/charming-actions' GitHub action for automated releases.
    # The test_deploy function in tests/integration/test_charm.py reads upstream-source
    # to determine which OCI image to use when running the charm's integration tests.
    upstream-source: ghcr.io/canonical/api_demo_server/api-demo-server:2.1.0
```

--------------------------------

### Deploy a charm in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Uses the Jubilant framework to deploy a charm and wait for it to reach an active state.

```python
import pathlib

import jubilant


@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    """Deploy the charm under test."""
    juju.deploy(charm)
    juju.wait(jubilant.all_active)
```

--------------------------------

### Initialize Harness with Pytest Fixture

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Use a pytest fixture to ensure the harness is properly cleaned up after each test execution.

```python
@pytest.fixture()
def harness():
    harness = Harness(MyCharm)
    yield harness
    harness.cleanup()
```

--------------------------------

### Migrate Status Fetching

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Transition from background websocket updates to explicit synchronous status calls.

```python
# pytest-operator
async def test_active(app: Application):
    assert app.units[0].workload_status == ActiveStatus.name


# jubilant
def test_active(juju: jubilant.Juju, app: str):
    status = juju.status()
    assert status.apps[app].units[app + '/0'].is_active
```

--------------------------------

### Run integration tests with file logging

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Enable file logging for a specific tox integration test run.

```text
tox -e integration -- --log-file logs/verbose.log
```

--------------------------------

### Integrate charm with PostgreSQL

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Establish the relation between the FastAPI charm and the PostgreSQL database.

```text
juju integrate postgresql-k8s fastapi-demo
```

--------------------------------

### Define containers and resources in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use this configuration to specify OCI images for multiple workload containers within a charm.

```yaml
# ...
containers:
  myapp:
    resource: myapp-image
  redis:
    resource: redis-image

resources:
  myapp-image:
    type: oci-image
    description: OCI image for my application
  redis-image:
    type: oci-image
    description: OCI image for Redis
# ...
```

--------------------------------

### Test adding a Pebble layer

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Simulate a pebble-ready event and verify that a new layer has been added to the container plan.

```python
def test_add_layer():
    ctx = testing.Context(MyCharm)
    layer = testing.layer_from_rockcraft('../rock/rockcraft.yaml')
    container_in = testing.Container('workload', layers=[layer])
    state_in = testing.State(containers={container_in})
    state_out = ctx.run(ctx.on.pebble_ready(container_in), state_in)
    container_out = state_out.get_container(container_in.name)
    assert len(container_out.layers) == 2
    new_plan = container_out.plan
    assert ...  # Verify that the plan contains changes made in pebble-ready.
```

--------------------------------

### Observe and respond to custom notices in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-custom-notices.md

Observe the pebble_custom_notice event in the charm's __init__ method and handle specific notice keys in the event handler.

```python
class PostgresCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        # Note that "db" is the workload container's name
        framework.observe(
            self.on['db'].pebble_custom_notice, self._on_pebble_custom_notice
        )

    def _on_pebble_custom_notice(
        self, event: ops.PebbleCustomNoticeEvent
    ) -> None:
        if event.notice.key == 'canonical.com/postgresql/backup-done':
            path = event.notice.last_data['path']
            logger.info('Backup finished, copying %s to the cloud', path)
            f = event.workload.pull(path, encoding=None)
            s3_bucket.upload_fileobj(f, 'db-backup.sql')

        elif event.notice.key == 'canonical.com/postgresql/other-thing':
            logger.info('Handling other thing')
```

--------------------------------

### Test charm actions with Context

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Uses Context.on.action to trigger a charm action and verify the resulting action output against the expected state.

```python
from ops import testing

from charm import DemoCharm


def test_get_db_endpoint_action():
    ctx = testing.Context(DemoCharm)
    relation = testing.Relation(
        endpoint='database',
        remote_app_data={'endpoints': 'bar.local:5678'},
    )
    state_in = testing.State(relations={relation})
    ctx.run(ctx.on.action('get-db-endpoint'), state_in)
    assert ctx.action_results == {'endpoint': 'bar.local:5678'}
```

--------------------------------

### ops.pebble.Client.exec

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Execute a command on the remote system.

```APIDOC
## exec(command: list[str], ...)

### Description
Execute the given command on the remote system. Returns an ExecProcess that handles either strings or bytes depending on the encoding parameter.

### Parameters
- **command** (list[str]) - Required - The command to execute.
- **service_context** (str) - Optional - Service context for the execution.
- **environment** (dict[str, str]) - Optional - Environment variables.
- **working_dir** (str | PurePath) - Optional - Working directory.
- **timeout** (float) - Optional - Execution timeout.
- **user_id/user/group_id/group** (int/str) - Optional - User/Group identity for execution.
- **stdin/stdout/stderr** (TextIO/BinaryIO) - Optional - Input/Output streams.
- **encoding** (str) - Optional - Encoding for string output (default 'utf-8').
```

--------------------------------

### Configure Charmcraft for Git Dependencies

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Add git as a build-package in charmcraft.yaml to support git-based dependencies.

```yaml
parts:
  charm:
    build-packages:
      - git
```

--------------------------------

### get_filesystem_root(container: str | Container) -> Path

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Returns the temporary directory path used by the harness to simulate the container's root filesystem.

```APIDOC
## get_filesystem_root(container: str | Container) -> Path

### Description
Returns the temp directory path harness will use to simulate the container filesystem. Charm tests should treat the returned directory as the container's root directory (/).

### Parameters
- **container** (str | Container) - Required - The name of the container or the container instance.

### Returns
- **Path** - The path of the temporary directory associated with the specified container.
```

--------------------------------

### Implement transitional Ops charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

A temporary approach mapping Ops events to legacy shell hooks using subprocess calls.

```python
#!/usr/bin/env python3
import os
import ops


class Microsample(ops.CharmBase):
    def __init__(self, framework):
        super().__init__(framework)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(self.on.install, self._on_install)
        framework.observe(self.on.start, self._on_start)
        framework.observe(self.on.stop, self._on_stop)
        # etc...

    def _on_config_changed(self, _event):
        os.popen('../hooks/config-changed')

    def _on_install(self, _event):
        os.popen('../hooks/install')

    def _on_start(self, _event):
        os.popen('../hooks/start')

    def _on_stop(self, _event):
        os.popen('../hooks/stop')


if __name__ == '__main__':
    ops.main(Microsample)
```

--------------------------------

### Invoke charm action

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Execute the get-db-info action on a specific unit.

```text
juju run fastapi-demo/0 get-db-info
```

--------------------------------

### Declare action in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Define the action schema, parameters, and validation rules in the charmcraft.yaml file.

```yaml
actions:
  snapshot:
    description: Take a snapshot of the database.
    params:
      filename:
        type: string
        description: The name of the snapshot file.
      compression:
        type: object
        description: The type of compression to use.
        properties:
          kind:
            type: string
            enum:
            - gzip
            - bzip2
            - xz
            default: gzip
          quality:
            description: Compression quality
            type: integer
            default: 5
            minimum: 0
            maximum: 9
    required:
    - filename
    additionalProperties: false
```

--------------------------------

### Upload logs as CI artifacts

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Use GitHub Actions to upload integration test logs as build artifacts.

```yaml
  # In your integration test job
  - run: tox -e integration -- --log-file logs/verbose.log
  - name: Upload logs
    if: ${{ !cancelled() }}
    uses: actions/upload-artifact@v7
    with:
      name: integration-test-logs
      path: logs
```

--------------------------------

### Inspect Kubernetes pods with kubectl

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Use these commands to investigate pod status, events, and logs when a unit is stuck before Pebble is reachable.

```shell
kubectl -n <model> get pods
kubectl -n <model> describe pod myapp-0        # events: image pulls, scheduling, OOM kills, restarts
kubectl -n <model> logs myapp-0 -c charm       # charm container stdout
kubectl -n <model> logs myapp-0 -c myapp       # workload container stdout (Pebble's own output)
kubectl -n <model> logs myapp-0 -c myapp --previous   # output from the last crashed instance
```

--------------------------------

### Update charm configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Set a new value for the server-port configuration option.

```text
juju config fastapi-demo server-port=5000
```

--------------------------------

### Inject a rescue shell via Pebble

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Push a statically-linked busybox binary into the container to gain an interactive shell when the image lacks one.

```shell
apt install busybox-static                          # on your local machine
pebble push /usr/bin/busybox /charm/bin/busybox     # into the workload container
pebble exec /charm/bin/busybox sh
# hostname
mycharm-0
```

--------------------------------

### Configure tox.ini for integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Defines the integration test environment and command execution settings in tox.ini.

```ini
[testenv:integration]
description = Run integration tests
runner = uv-venv-lock-runner
dependency_groups =
    integration
pass_env =
    # The integration tests don't pack the charm. If CHARM_PATH is set, the tests deploy the
    # specified .charm file. Otherwise, the tests look for a .charm file in the project dir.
    CHARM_PATH
commands =
    pytest \
        -v \
        -s \
        --tb native \
        --log-cli-level=INFO \
        {[vars]tests_path}/integration \
        {posargs}
```

--------------------------------

### Configure verbose logging in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Includes timestamps in the log output by defining a date format and log format.

```toml
[tool.pytest.ini_options]
...
log_cli_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
log_cli_date_format = "%Y-%m-%dT%H:%M:%SZ"
```

--------------------------------

### Add cosl dependency

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Update the charm's dependencies using uv to include the required cosl package.

```text
uv add 'cosl>=1.9.1,<2'
```

--------------------------------

### Define metrics configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Create a YAML file to specify the secret ID for the metrics charm.

```yaml
metrics-charm:
  metrics-secret-id: <secret-id-here>
```

--------------------------------

### Add APT dependency to pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Include the charmlibs-apt library in your project dependencies.

```toml
dependencies = [
    "charmlibs-apt>=1,<2",
    # ...
]
```

--------------------------------

### ops.testing.Harness

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

The Harness class is the primary entry point for testing charms, allowing you to build a model and simulate Juju events.

```APIDOC
## ops.testing.Harness(charm_cls, meta=None, actions=None, config=None)

### Description
Initializes the test harness for a specific charm class. This class allows you to simulate the Juju model environment for testing purposes.

### Parameters
- **charm_cls** (type[CharmType]) - Required - The Charm class to test.
- **meta** (str | TextIO) - Optional - Contents of metadata.yaml.
- **actions** (str | TextIO) - Optional - Contents of actions.yaml.
- **config** (str | TextIO) - Optional - Contents of config.yaml.
```

--------------------------------

### Virtual machine shell prompt

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

The command prompt indicating active session inside the VM.

```text
ubuntu@juju-sandbox-k8s:~$
```

--------------------------------

### Create a Pydantic configuration model

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Define a Pydantic model in src/charm.py to mirror configuration options for type checking and validation.

```python
class WikiConfig(pydantic.BaseModel):
    name: str = pydantic.Field('Wiki')
    skin: str = pydantic.Field('vector')

    @pydantic.validator('name')
    def validate_name(cls, value):
        if len(value) < 4:
            raise ValueError('Name must be at least 4 characters long')
        if ' ' in value:
            raise ValueError('Name must not contain spaces')
        return value
```

--------------------------------

### Test library initialization

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Validates that a charm can initialize the library without emitting unexpected events during standard lifecycle hooks.

```python
import pytest
import ops
from ops import testing
from lib.charms.my_charm.v0.my_lib import DatabaseReadyEvent, DatabaseRequirer


class MyTestCharm(ops.CharmBase):
    META = {
        'name': 'my-charm',
        'requires': {'my-relation': {'interface': 'database'}},
    }

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.db = DatabaseRequirer(self, endpoint='my-relation')


@pytest.mark.parametrize(
    'event',
    (
        'start',
        'install',
        'stop',
        'remove',
        'update_status',  # ...
    ),
)
def test_charm_runs(event):
    """Verify that the charm can create the library object, and doesn't see unexpected events."""
    ctx = testing.Context(MyTestCharm, meta=MyTestCharm.META)
    state_in = testing.State()
    ctx.run(getattr(ctx.on, event)(), state_in)
    # The Juju event itself is always emitted; what matters is that the library
    # doesn't emit any of its own events when the database isn't ready.
    assert not any(
        isinstance(e, DatabaseReadyEvent) for e in ctx.emitted_events
    )
```

--------------------------------

### Filter logs with multiple modules

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Combine multiple include flags to build precise log filters for specific operations.

```shell
juju debug-log --debug \
  --include-module juju.worker.uniter.operation \
  --include-module unit.myapp/0.juju-log
```

--------------------------------

### Stream input and output to files

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Provides input via stdin and redirects output to files using standard Python file handles.

```python
>>> stdin = 'foo\nbar\n'
>>> with open('out.txt', 'w') as out, open('err.txt', 'w') as err:
...     process = client.exec(['awk', '{ print toupper($0) }'],
...                           stdin=stdin, stdout=out, stderr=err)
...     process.wait()
>>> open('out.txt').read()
'FOO\nBAR\n'
>>> open('err.txt').read()
''
```

--------------------------------

### Integrate applications

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Replaces async-based relation management with synchronous integration calls.

```python
# pytest-operator
await asyncio.gather(
    model.add_relation('discourse-k8s', 'postgresql-k8s:database'),
    model.add_relation('discourse-k8s', 'redis-k8s'),
    model.add_relation('discourse-k8s', 'nginx-ingress-integrator'),
)
await model.wait_for_idle(status='active')

# jubilant
juju.integrate('discourse-k8s', 'postgresql-k8s:database')
juju.integrate('discourse-k8s', 'redis-k8s')
juju.integrate('discourse-k8s', 'nginx-ingress-integrator')
juju.wait(jubilant.all_active)
```

--------------------------------

### Extend charm-libs in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Add the required observability libraries to the charm-libs section of your charmcraft.yaml file.

```yaml
charm-libs:
  - lib: data_platform_libs.data_interfaces
    version: "0"
  - lib: grafana_k8s.grafana_dashboard
    version: "0"
  - lib: loki_k8s.loki_push_api
    version: "1"
  - lib: observability_libs.juju_topology
    version: "0"
  - lib: prometheus_k8s.prometheus_scrape
    version: "0"
```

--------------------------------

### List files with Container.list_files

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Retrieve file information objects for entries in a directory, optionally filtered by a glob pattern.

```python
infos = self.container.list_files('/etc/myapp', pattern='*.yaml')
total_size = sum(f.size for f in infos)
logger.info('total size of files: %d', total_size)
names = set(f.name for f in infos)
```

--------------------------------

### Full Pebble-ready test

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Complete test function including service and status verification.

```python
def test_pebble_ready():
    ctx = testing.Context(DemoCharm)
    container_in = testing.Container('my-container', can_connect=True)
    state_in = testing.State(containers={container_in})
    state_out = ctx.run(ctx.on.pebble_ready(container_in), state_in)
    container_out = state_out.get_container(container_in.name)
    assert 'workload' in container_out.plan.services
    assert container_out.plan.services['workload'].command == 'run-workload'
    assert state_out.unit_status == testing.ActiveStatus()
```

--------------------------------

### Run Pebble commands from the charm container

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Connect to the charm container and point the PEBBLE_SOCKET to the workload's socket to execute Pebble commands.

```shell
juju ssh myapp/0   # connects to the charm container by default
export PEBBLE_SOCKET=/charm/myapp/pebble.sock   # point at the workload's Pebble
/charm/bin/pebble services
/charm/bin/pebble logs
/charm/bin/pebble exec -- cat /etc/myapp/config.yaml
```

--------------------------------

### Simulate Container Command Execution

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Register handlers or static results to simulate Pebble command execution within a container. The longest matching command prefix takes precedence.

```python
# produce no output and return 0 for every command
harness.handle_exec('container', [], result=0)

# simple example that just produces output (exit code 0)
harness.handle_exec('webserver', ['ls', '/etc'], result='passwd\nprofile\n')

# slightly more complex (use stdin)
harness.handle_exec(
    'c1', ['sha1sum'],
    handler=lambda args: ExecResult(stdout=hashlib.sha1(args.stdin).hexdigest()))

# more complex example using args.command
def docker_handler(args: testing.ExecArgs) -> testing.ExecResult:
    match args.command:
        case ['docker', 'run', image]:
            return testing.ExecResult(stdout=f'running {image}')
        case ['docker', 'ps']:
            return testing.ExecResult(stdout='CONTAINER ID   IMAGE ...')
        case _:
            return testing.ExecResult(exit_code=1, stderr='unknown command')

harness.handle_exec('database', ['docker'], handler=docker_handler)

# handle timeout
def handle_timeout(args: testing.ExecArgs) -> int:
    if args.timeout is not None and args.timeout < 10:
        raise TimeoutError
    return 0

harness.handle_exec('database', ['foo'], handler=handle_timeout)
```

--------------------------------

### Access storage instances with pathops

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use pathops or standard file operations to interact with the mounted storage paths.

```python
# Prepare each storage instance for use by the workload.
for path in cache_paths:
    cache_root = pathops.LocalPath(path)
    (cache_root / 'uploaded-data').mkdir(exist_ok=True)
    (cache_root / 'processed-data').mkdir(exist_ok=True)
```

--------------------------------

### Upload logs as CI artifacts

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Configure a GitHub Actions job to capture logs and upload them as artifacts even if the test fails.

```yaml
  # In your integration test job
  - run: tox -e integration -- --log-file logs/verbose.log --juju-dump-logs logs
  - name: Upload logs
    if: ${{ !cancelled() }}
    uses: actions/upload-artifact@v7
    with:
      name: integration-test-logs
      path: logs
```

--------------------------------

### Signal a directly-launched process to reload configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Uses os.kill to send a SIGUSR1 signal to a process identified by a PID file.

```python
import os
import signal

from charmlibs import pathops

PID_FILE = pathops.LocalPath('/var/run/myworkload.pid')


def reload_config() -> None:
    pid = int(PID_FILE.read_text())
    os.kill(pid, signal.SIGUSR1)
```

--------------------------------

### Observe database events

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Register event observers for database creation and endpoint changes.

```python
# See https://charmhub.io/data-platform-libs/libraries/data_interfaces
framework.observe(self.database.on.database_created, self._on_database_endpoint)
framework.observe(self.database.on.endpoints_changed, self._on_database_endpoint)
```

--------------------------------

### Update State and Container attribute names

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Update State and Container initialization to use pluralized attribute names and the new Exec class.

```python
# Older Scenario code
state = State(stored_state=[ss1, ss2], storage=[s1, s2])

# Scenario 7.x
state = State(stored_states={s1, s2}, storages={s1, s2})
```

```python
# Older Scenario code
container = Container(
    name="foo",
    exec_mock={("ls", "-ll"): ExecOutput(return_code=0, stdout=....)},
    service_status={"srv1": ops.pebble.ServiceStatus.ACTIVE}
)

# Scenario 7.x
container = Container(
    name="foo",
    execs={Exec(["ls", "-ll"], return_code=0, stdout=....)},
    service_statuses={"srv1": ops.pebble.ServiceStatus.ACTIVE},
)
```

--------------------------------

### Test charms using charmcraft extensions

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Automatically expand charmcraft extensions by passing the charm class to Context, allowing access to extension-provided relations.

```python
# Given a charmcraft.yaml with:
#   extensions:
#     - flask-framework

ctx = testing.Context(MyFlaskCharm)
# The 'ingress' relation is provided by the flask-framework extension.
state = ctx.run(
    ctx.on.start(), testing.State(relations={testing.Relation('ingress')})
)
```

--------------------------------

### Write functional tests for workload modules

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Functional tests exercise the workload module against real system components like apt, snap, and systemd without Juju.

```python
# tests/functional/test_myworkload.py
import subprocess

from charm import myworkload


def test_install_and_start():
    assert not myworkload.is_installed()
    myworkload.install()
    assert myworkload.is_installed()
    assert myworkload.get_version() == '1.11.1'

    myworkload.start()
    assert myworkload.is_running()

    # The real systemd unit should be active.
    result = subprocess.run(
        ['/usr/bin/systemctl', 'is-active', 'tinyproxy'],
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == 'active'

    myworkload.stop()
    assert not myworkload.is_running()
```

--------------------------------

### Push files and directories to remote

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Use push_path to copy local files or directories to a remote destination. Supports glob patterns and multiple source paths.

```default
# copy one file
container.push_path('/foo/foobar.txt', '/dst')
# Destination results: /dst/foobar.txt

# copy a directory
container.push_path('/foo', '/dst')
# Destination results: /dst/foo/bar/baz.txt, /dst/foo/foobar.txt

# copy a directory's contents
container.push_path('/foo/*', '/dst')
# Destination results: /dst/bar/baz.txt, /dst/foobar.txt

# copy multiple files
container.push_path(['/foo/bar/baz.txt', 'quux.txt'], '/dst')
# Destination results: /dst/baz.txt, /dst/quux.txt

# copy a file and a directory
container.push_path(['/foo/bar', '/quux.txt'], '/dst')
# Destination results: /dst/bar/baz.txt, /dst/quux.txt
```

--------------------------------

### Implement custom instrumentation with OpenTelemetry

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Use the tracer object to create spans and add events for granular monitoring of specific methods.

```python
import opentelemetry.trace

tracer = opentelemetry.trace.get_tracer(__name__)


class Workload:
    ...

    def migrate_db(self):
        with tracer.start_as_current_span('migrate-db') as span:
            for attempt in range(3):
                try:
                    subprocess.check_output('/path/to/migrate.sh')
                except subprocess.CalledProcessError:
                    span.add_event('db-migrate-failed', {'attempt': attempt})
                    time.sleep(10**attempt)
                else:
                    break
            else:
                logger.error('Could not migrate the database')
            ...
```

--------------------------------

### Inspect requested storage volumes

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use the Context.requested_storage API to verify that a charm has requested the expected number of storage volumes during an event.

```python
ctx = testing.Context(MyCharm)
ctx.run(ctx.on.some_event_that_will_request_more_storage(), testing.State())

# The charm has requested two 'foo' storage volumes to be provisioned:
assert ctx.requested_storages['foo'] == 2
```

--------------------------------

### Avoid StoredState for configuration tracking

Source: https://github.com/canonical/operator/blob/main/docs/explanation/storedstate-guidance.md

This pattern is discouraged as it introduces redundant state tracking, increasing the risk of synchronization bugs.

```python
def __init__(self, framework: ops.Framework):
    super().__init__(framework)
    framework.observe(self.on.config_changed, self._on_config_changed)
    self._stored.set_default(current_mode='test')

def _on_config_changed(self, event):
    mode = self.config['mode']
    if self._stored.current_mode == mode:
        return
    if mode not in ('production', 'test'):
        self.unit.status = ops.BlockedStatus(f'Invalid mode: {mode!r})
        return

    with open('/etc/example_blog/mode', 'w') as mode_file:
        mode_file.write('{}
'.format(mode)

    self._restart()

    self._stored.current_mode = mode
```

--------------------------------

### Repack and refresh charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Use these commands to update the deployed charm with new changes.

```text
charmcraft pack
juju refresh fastapi-demo --force-units \
  --path ./fastapi-demo_amd64.charm \
  --resource demo-server-image=ghcr.io/canonical/api_demo_server/api-demo-server:2.1.0
```

--------------------------------

### Test storage attachment with jubilant

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use this test pattern to verify that storage units are correctly added to a charm unit and that the system reaches an active state.

```python
def test_storage_attaching(juju: jubilant.Juju):
    # Add two storage units of 2 gigabyte each to unit 0 of the Kafka app.
    juju.cli('add-storage', 'kafka/0', 'data=2G,2', include_model=True)
    juju.wait(jubilant.all_active)
    # Assert that the storage is being used appropriately.
```

--------------------------------

### attach_storage

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Simulates a juju attach-storage call for a specific storage unit.

```APIDOC
## attach_storage(storage_id: str)

### Description
Attach a storage device. If called after begin() and hooks are not disabled, it will trigger a storage-attached hook.

### Parameters
- **storage_id** (str) - Required - The full storage ID of the storage unit being attached.
```

--------------------------------

### Configure pytest logging in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Set up verbose file logging and console log levels within the pytest configuration.

```toml
[tool.pytest.ini_options]
...

# Retain INFO logs in the "Captured log call" section when run interactively.
# Otherwise, that section will have DEBUG logs (coming from log_file_level).
log_level = "INFO"

log_cli_format = "%(levelname)s %(name)s %(message)s"

log_file_level = "DEBUG"
log_file_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
log_file_date_format = "%Y-%m-%dT%H:%M:%SZ"
```

--------------------------------

### Initialize and use a logger in a charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/log-from-your-charm.md

Define a logger at the module level and use it within charm event handlers to record state changes.

```python
import logging

...
logger = logging.getLogger(__name__)


class HelloOperatorCharm(ops.CharmBase):
    ...

    def _on_config_changed(self, _):
        current = self.config['thing']
        if current not in self._stored.things:
            # Note the use of the logger here:
            logger.info('Found a new thing: %r', current)
            self._stored.things.append(current)
```

--------------------------------

### Populate State.deferred using .deferred()

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Use the .deferred() method directly on Juju events to ensure proper linking of deferred events.

```python
# Older Scenario code
deferred_start = scenario.deferred('start', handler=MyCharm._on_start)
deferred_relation_created = Relation('foo').changed_event.deferred(
    handler=MyCharm._on_foo_relation_changed
)
deferred_config_changed = DeferredEvent(
    handle_path='MyCharm/on/config_changed[1]', owner='MyCharm', observer='_on_config_changed'
)

# Scenario 7.x
deferred_start = ctx.on.start().deferred(handler=MyCharm._on_start)
deferred_relation_changed = ctx.on.relation_changed(Relation('foo')).deferred(
    handler=MyCharm._on_foo_relation_changed
)
deferred_config_changed = ctx.on.config_changed().deferred(handler=MyCharm._on_config_changed)
```

--------------------------------

### restart(*service_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Restart the given service(s) by name.

```APIDOC
## restart(*service_names: str)

### Description
Restart the given service(s) by name. Listed running services will be stopped and restarted, and listed stopped services will be started.
```

--------------------------------

### ops.hookcmds.state_get(key: str | None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves server-side-state values.

```APIDOC
## ops.hookcmds.state_get(key: str | None)

### Description
Get server-side-state value.

### Parameters
- **key** (str | None) - Optional - The key of the server-side state to get. If None, get all keys and values.
```

--------------------------------

### Add and grant access to a secret

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Implementation of secret creation and access granting using the ops framework.

```python
class MyDatabaseCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(
            self.on.database_relation_joined, self._on_database_relation_joined
        )

    ...  # other methods and event handlers

    def _on_database_relation_joined(self, event: ops.RelationJoinedEvent):
        content = {
            'username': 'admin',
            'password': 'admin',
        }
        secret = self.app.add_secret(content)
        secret.grant(event.relation)
        event.relation.data[self.app]['secret-id'] = secret.id
```

--------------------------------

### Define a minimal charm class for testing

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

A sample charm class implementing a 'get-value' action that can succeed or fail based on input parameters.

```python
class DemoCharm(ops.CharmBase):
    """Manage the workload."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        framework.observe(
            self.on['get-value'].action, self._on_get_value_action
        )

    def _on_get_value_action(self, event: ops.ActionEvent) -> None:
        """Handle the get-value action."""
        if event.params['value'] == 'please fail':
            event.fail('Action failed, as requested')
        else:
            event.set_results({'out-value': event.params['value']})
```

--------------------------------

### Configure charmcraft for legacy mode

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

A charmcraft.yaml configuration used to support older charm frameworks by explicitly including files in the prime section.

```yaml
parts:
  microsample:
    plugin: dump
    source: .
    prime:
      - LICENSE
      - README.md
      - config.yaml
      - copyright
      - hooks
      - icon.svg
      - metadata.yaml
```

--------------------------------

### Test leadership status in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-leadership-changes.md

Use testing.Context and State to simulate leader and non-leader scenarios during unit testing.

```python
class MyCharm(ops.CharmBase):
    def __init__(self, framework):
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)

    def _on_start(self, _):
        if self.unit.is_leader():
            self.unit.status = ops.ActiveStatus('I rule')
        else:
            self.unit.status = ops.ActiveStatus('I am ruled')


@pytest.mark.parametrize('leader', (True, False))
def test_status_leader(leader):
    ctx = testing.Context(MyCharm, meta={'name': 'foo'})
    out = ctx.run(ctx.on.start(), testing.State(leader=leader))
    assert out.unit_status == testing.ActiveStatus(
        'I rule' if leader else 'I am ruled'
    )
```

--------------------------------

### Request storage instances in charm code

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Programmatically request additional storage instances using the ops framework.

```python
self.model.storages.request('cache', 2)  # Request two more instances.
```

--------------------------------

### ops.hookcmds.action_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves action parameters, optionally recursing into a dotted key.

```APIDOC
## ops.hookcmds.action_get(key: str | None = None) -> dict[str, Any] | Any

### Description
Get action parameters. If a dotted key (for example foo.bar) is passed, action_get will recurse into the parameter map as needed.

### Parameters
- **key** (str) - Optional - The key of the action parameter to retrieve. If not provided, all parameters will be returned.
```

--------------------------------

### Specify a custom charm root directory

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Provide a custom charm_root directory to the Context constructor to control where metadata files are written.

```python
import tempfile


class MyCharmType(ops.CharmBase):
    pass


td = tempfile.TemporaryDirectory()
ctx = testing.Context(
    charm_type=MyCharmType,
    meta={'name': 'my-charm-name'},
    charm_root=td.name,
)
state = ctx.run(ctx.on.start(), testing.State())
```

--------------------------------

### Add simulated network data

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Configures network information for a specific binding or the default binding.

```default
# Set network info for default binding
harness.add_network('10.0.0.10')

# Or set network info for specific endpoint
harness.add_network('10.0.0.10', endpoint='db')
```

```default
binding = harness.model.get_binding('db')
assert binding.network.bind_address == ipaddress.IPv4Address('10.0.0.10'))
```

--------------------------------

### Execute process with raw bytes

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Set encoding to None to handle raw bytes instead of Unicode strings.

```python
process = container.exec(['cat'], stdin=b'\x01\x02', encoding=None)
stdout, _ = process.wait_output()
logger.info('Output: %r', stdout)
```

--------------------------------

### Real-time streaming with stdin and stdout

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Uses threads to write to stdin and iterates over stdout for real-time process interaction.

```python
>>> process = client.exec(['cat'])
>>> def stdin_thread():
...     for line in ['one\n', '2\n', 'THREE\n']:
...         process.stdin.write(line)
...         process.stdin.flush()
...         time.sleep(1)
...     process.stdin.close()
...
>>> threading.Thread(target=stdin_thread).start()
>>> for line in process.stdout:
...     print(datetime.datetime.now().strftime('%H:%M:%S'), repr(line))
...
16:20:26 'one\n'
16:20:27 '2\n'
16:20:28 'THREE\n'
>>> process.wait()  # will return immediately as stdin was closed
```

--------------------------------

### Implement config-changed handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Method to handle configuration changes by re-running the configuration logic.

```python
    def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
        """Handle config-changed event."""
        self.configure_and_run()
```

--------------------------------

### Verify interface registration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Expected output when running the interface tester to verify the schema.

```yaml
- my_fancy_database:
  - v0:
   - provider:
     - <no tests>
     - schema OK
     - charms:
       - my_fancy_database_charm (https://github.com/your-github-slug/my-fancy-database-operator) custom_test_setup=no
   - requirer:
     - <no tests>
     - schema OK
     - <no charms>
```

--------------------------------

### Copy a directory tree to the container

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use push_path to copy files recursively into a destination directory, supporting trailing globbing.

```python
# copy "/source/dir/[files]" into "/destination/dir/[files]"
self.container.push_path('/source/dir', '/destination')

# copy "/source/dir/[files]" into "/destination/[files]"
self.container.push_path('/source/dir/*', '/destination')
```

--------------------------------

### Implement a charm fixture in conftest.py

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Provides a session-scoped fixture to locate the charm file for deployment during integration tests.

```python
import os
import pathlib

import pytest


@pytest.fixture(scope='session')
def charm():
    """Return the path of the charm under test."""
    charm = os.environ.get('CHARM_PATH')
    if not charm:
        charm_dir = (
            pathlib.Path()
        )  # Assume the current working directory is the charm root.
        charms = list(charm_dir.glob('*.charm'))
        assert charms, f'No charms were found in {charm_dir.absolute()}'
        assert len(charms) == 1, f'Found more than one charm {charms}'
        charm = charms[0]
    path = pathlib.Path(charm).resolve()
    assert path.is_file(), f'{path} is not a file'
    return path
```

--------------------------------

### Initialize debugpy listener in charm.py

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Add this snippet to the top of your charm module to enable remote debugging when JUJU_DEBUG_AT is set.

```python
import os

if os.getenv('JUJU_DEBUG_AT'):
    import debugpy
    debugpy.listen(('0.0.0.0', 5678))
    debugpy.wait_for_client()
```

--------------------------------

### Read from database via API

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Retrieve data from the application to verify database read operations.

```text
curl 10.1.157.90:8000/names
```

--------------------------------

### Toggle service mode via config change

Source: https://github.com/canonical/operator/blob/main/docs/explanation/storedstate-guidance.md

Updates a local configuration file based on charm config and restarts the service.

```python
def _on_config_changed(self, event: ops.ConfigChangedEvent):
    mode = self.config['mode']
    if mode not in ('production', 'test'):
        self.unit.status = ops.BlockedStatus(f'Invalid mode: {mode!r})
        return

    with open('/etc/example_blog/mode', 'w') as mode_file:
        mode_file.write(f'{mode}\n')

    self._restart()
```

--------------------------------

### Observe action event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Register the action event observer within the charm's __init__ method.

```default
framework.observe(self.on['snapshot'].action, self._on_snapshot_action)
```

--------------------------------

### add_resource

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Registers content for a resource to the backend for testing.

```APIDOC
## add_resource(resource_name: str, content: AnyStr)

### Description
Add content for a resource to the backend. This will register the content, so that a call to model.resources.fetch(resource_name) will return a path to a file containing that content.

### Parameters
- **resource_name** (str) - Required - The name of the resource being added.
- **content** (AnyStr) - Required - Either string or bytes content.
```

--------------------------------

### Write unit tests for stored state

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Use ops.testing.PeerRelation and testing.State to verify that the charm correctly interacts with peer relation data.

```python
def test_charm_sets_stored_state():
    ctx = testing.Context(MyCharm)
    peer = testing.PeerRelation('charm-peer')
    state_in = testing.State(relations={peer})
    state_out = ctx.run(ctx.on.start(), state_in)
    rel = state_out.get_relation(peer.id)
    assert rel.local_app_data['expensive_value'] == '42'
```

--------------------------------

### Configure integration test environment in tox.ini

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Define the integration test environment in tox.ini to pass the charm path via environment variables.

```ini
[testenv:integration]
pass_env =
    CHARM_PATH
commands =
    pytest --tb=native -vv --log-cli-level=DEBUG {toxinidir}/tests/integration {posargs}
```

--------------------------------

### Define dependencies in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Specify direct dependencies and development groups in the project configuration file.

```toml
# All dependencies required to run the charm
dependencies = [
    "ops>=3,<4",
]

[dependency-groups]
# Dependencies of linting and static type checks
lint = [
    "ruff",
    "codespell",
    "pyright",
]
# Dependencies of unit tests
unit = [
    "coverage[toml]",
    "ops[testing]",
    "pytest",
]
# Dependencies of integration tests
integration = [
    "jubilant>=1.8,<2",
    "pytest-jubilant>=2,<3",
]
# Additional groups
docs = [
    "Sphinx",
]
```

--------------------------------

### Replace copy and replace methods

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Use dataclasses.replace and copy.deepcopy instead of the removed .replace() and .copy() methods on State components.

```python
# Older Scenario code.
new_container = container.replace(can_connect=True)
duplicate_relation = relation.copy()

# Scenario 7.x
new_container = dataclasses.replace(container, can_connect=True)
duplicate_relation = copy.deepcopy(relation)
```

--------------------------------

### Mocking external dependencies with pytest

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Use a pytest fixture to patch external clients like lightkube before initializing the charm.

```python
from unittest.mock import MagicMock, patch

import pytest
from ops import testing

from charm import MyCharm


@pytest.fixture
def my_charm():
    with patch('charm.lightkube.Client'):
        yield MyCharm
```

--------------------------------

### ops.hookcmds.status_get(*, app: bool = False)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves the status of a unit or an application.

```APIDOC
## ops.hookcmds.status_get(*, app: bool = False)

### Description
Get a status of a unit or an application.

### Parameters
- **app** (bool) - Optional - Get status for all units of this application if this unit is the leader.
```

--------------------------------

### Stop virtual machine

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Shuts down the specified virtual machine.

```text
multipass stop juju-sandbox
```

--------------------------------

### Implement a custom event in a library

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Define custom events by inheriting from ops.EventBase and emitting them via ops.EventSource.

```python
class DatabaseReadyEvent(ops.EventBase):
    """Event representing that the database is ready."""

    def __init__(self, handle: ops.Handle, *, credential_secret: ops.Secret):
        super().__init__(handle)
        self.credential_secret = credential_secret

    def snapshot(self) -> dict[str, str]:
        data = super().snapshot()
        data['credential_secret_id'] = self.credential_secret.id
        return data

    def restore(self, snapshot: dict[str, Any]):
        super().restore(snapshot)
        credential_secret_id = snapshot['credential_secret_id']
        self.credential_secret = self.framework.model.get_secret(
            id=credential_secret_id
        )


class DatabaseRequirerEvents(ops.ObjectEvents):
    """Container for Database Requirer events."""

    ready = ops.EventSource(DatabaseReadyEvent)


class DatabaseRequirer(ops.Object):
    on = DatabaseRequirerEvents()

    def __init__(self, charm: ops.CharmBase, endpoint: str = 'database'):
        super().__init__(charm, endpoint)
        self.framework.observe(
            charm.on[endpoint].relation_changed, self._on_db_changed
        )

    def _on_db_changed(self, event: ops.RelationChangedEvent):
        if remote_data_is_valid(event.relation):
            secret = ...
            self.on.ready.emit(credential_secret=secret)
```

--------------------------------

### ops.hookcmds.goal_state

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Print the status of the charm’s peers and related units.

```APIDOC
## ops.hookcmds.goal_state()

### Description
Print the status of the charm’s peers and related units.
```

--------------------------------

### get_notices

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Query for notices that match all of the provided filters.

```APIDOC
## get_notices(users=None, user_id=None, types=None, keys=None)

### Description
Query for notices that match all of the provided filters. If no filters are specified, returns notices viewable by the requesting user.

### Parameters
- **users** (NoticesUsers | None) - Optional - Change which users’ notices to return.
- **user_id** (int | None) - Optional - Filter for notices for the specified user (Pebble admins only).
- **types** (Iterable[NoticeType | str] | None) - Optional - Filter for notices with any of the specified types.
- **keys** (Iterable[str] | None) - Optional - Filter for notices with any of the specified keys.

### Returns
- **list[Notice]** - A list of matching notices.
```

--------------------------------

### View service logs

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Retrieve stdout and stderr logs from services, with options for following or viewing all buffered output.

```shell
/charm/bin/pebble logs         # last 30 lines from all services
/charm/bin/pebble logs -f      # tail and follow
/charm/bin/pebble logs -n all  # show all buffered output
```

--------------------------------

### Validate configuration in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Use the jubilant library to update charm configuration and wait for the expected unit status transitions.

```python
import pathlib

import jubilant


def test_config_invalid_name(charm: pathlib.Path, juju: jubilant.Juju):
    original_name = juju.config('your-app')['name']
    try:
        juju.config('your-app', {'name': 'invalid name has spaces'})
        # A name with spaces should put the charm into blocked status.
        # Setting an invalid name should be caught by the charm and rejected
        # immediately. The timeout is overridden to test this fail-fast behavior.
        juju.wait(jubilant.all_blocked, timeout=10)
    finally:
        # Reset the config to bring the charm out of blocked status.
        juju.config('your-app', {'name': original_name})
        juju.wait(jubilant.all_active)


def test_config_valid_name(charm: pathlib.Path, juju: jubilant.Juju):
    juju.config('your-app', {'name': 'charming-wiki'})
    juju.wait(jubilant.all_active)
```

--------------------------------

### Unit test Pebble custom notices

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-custom-notices.md

Use the testing.Context and testing.Notice classes to simulate notice events and verify charm behavior.

```python
from ops import testing


@patch('charm.s3_bucket.upload_fileobj')
def test_backup_done(upload_fileobj):
    # Arrange:
    ctx = testing.Context(PostgresCharm)

    notice = testing.Notice(
        'canonical.com/postgresql/backup-done',
        last_data={'path': '/tmp/mydb.sql'},
    )
    container = testing.Container(
        'db',
        can_connect=True,
        notices=[
            testing.Notice(key='example.com/a', occurrences=10),
            testing.Notice(key='example.com/b'),
            notice,
        ],
    )
    root = container.get_filesystem()
    (root / 'tmp').mkdir()
    (root / 'tmp' / 'mydb.sql').write_text('BACKUP')
    state_in = testing.State(containers={container})

    # Act:
    state_out = ctx.run(
        ctx.on.pebble_custom_notice(container, notice), state_in
    )

    # Assert:
    upload_fileobj.assert_called_once()
    upload_f, upload_key = upload_fileobj.call_args.args
    self.assertEqual(upload_f.read(), b'BACKUP')
    self.assertEqual(upload_key, 'db-backup.sql')
```

--------------------------------

### Handle charmcraft packing error

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Error message encountered when required files are missing during the packing process.

```bash
Processing error: Failed to copy '/root/stage/src': no such file or directory.
```

--------------------------------

### Access storage instance in charm container

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use pathops or standard file operations to interact with the storage instance within the charm container.

```python
# Prepare the storage instance for use by the workload.
charm_cache_path = cache[0].location  # Always index 0 in a K8s charm.
charm_cache_root = pathops.LocalPath(charm_cache_path)
(charm_cache_root / 'uploaded-data').mkdir(exist_ok=True)
(charm_cache_root / 'processed-data').mkdir(exist_ok=True)
```

--------------------------------

### pull(path: str | PurePath, *, encoding: str = 'utf-8') → TextIO

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Reads a file's content from the remote system. The returned object is a context manager.

```APIDOC
## pull(path: str | PurePath, *, encoding: str = 'utf-8')

### Description
Read a file's content from the remote system. The returned object is a context manager; use `with` so the underlying file is closed promptly.

### Parameters
- **path** (str | PurePath) - Required - Path of the file to read from the remote system.
- **encoding** (str) - Optional - Encoding to use for decoding the file's bytes to string, or None to specify no decoding.

### Returns
A readable file-like object.

### Example
```python
with container.pull('/etc/config.yaml') as f:
    content = f.read()
```
```

--------------------------------

### ops.hookcmds.action_set

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Sets the results for an action.

```APIDOC
## ops.hookcmds.action_set(results: Mapping[str, Any])

### Description
Set action results.

### Parameters
- **results** (Mapping[str, Any]) - Required - The results map of the action, provided to the Juju user.
```

--------------------------------

### Activate specific breakpoints via CLI

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Use the --at flag to target specific breakpoints defined in the charm code.

```shell
juju debug-code --at=config-start myapp/0 config-changed
```

--------------------------------

### Verify service status

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Check that the service is active after replan.

```python
...
assert (
    container_out.service_statuses['workload']
    == ops.pebble.ServiceStatus.ACTIVE
)
```

--------------------------------

### Write Positive Path Test

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Verifies that the provider correctly validates and publishes data when the remote end meets the contract.

```python
import json

from interface_tester import Tester
from scenario import State, Relation


def test_contract_happy_path():
    # GIVEN that the remote end has requested tables in the right format
    tables_json = json.dumps(['users', 'passwords'])
    t = Tester(
        State(
            leader=True,
            relations=[
                Relation(
                    endpoint='my-fancy-database',  # the name doesn't matter
                    interface='my_fancy_database',
                    remote_app_data={'tables': tables_json},
                )
            ],
        )
    )
    # WHEN the database charm receives a relation-changed event
    state_out = t.run('my-fancy-database-relation-changed')
    # THEN the schema is satisfied (the database charm published all required fields)
    t.assert_schema_valid()
```

--------------------------------

### Expose Pebble port in charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Use set_ports in the charm code to expose the Pebble HTTP port.

```python
    self.unit.set_ports(38813)
```

--------------------------------

### Define storage in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Define a storage resource with multiple instances allowed, specifying type, properties, and size constraints.

```yaml
storage:
  cache:
    description: Somewhere to cache files locally.
    type: filesystem
    properties:
      - transient
    minimum-size: 1G
    multiple:
      range: 1-10
```

--------------------------------

### Configure icon inclusion in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/publish-your-charm-on-charmhub.md

Use the dump plugin to include an icon.svg file in the charm package when using the uv plugin.

```yaml
parts:
  charm:
    plugin: uv
    source: .
    build-snaps:
      - astral-uv
  extra-files:
    plugin: dump
    source: .
    stage:
      - icon.svg
```

--------------------------------

### Implement collect-unit-status handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Method to report the current status of the tinyproxy service to Juju.

```python
    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        """Report the status of tinyproxy (runs after each event)."""
        try:
            self.load_config(TinyproxyConfig)
        except pydantic.ValidationError as e:
            (slug_error,) = e.errors()  # 'slug' is the first and only option validated.
            slug_value = slug_error["input"]
            message = f"Invalid slug: '{slug_value}'. Slug must match the regex [a-z0-9-]+"
            event.add_status(ops.BlockedStatus(message))
        if not tinyproxy.is_installed():
            event.add_status(ops.MaintenanceStatus("Waiting for tinyproxy to be installed"))
        if not tinyproxy.is_running():
            event.add_status(ops.MaintenanceStatus("Waiting for tinyproxy to start"))
        event.add_status(ops.ActiveStatus())
```

--------------------------------

### add_oci_resource(resource_name, contents)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Registers an OCI resource and creates a temporary file for processing metadata.

```APIDOC
## add_oci_resource

### Description
Add OCI resources to the backend. This will register an OCI resource and create a temporary file for processing metadata about the resource.

### Parameters
- **resource_name** (str) - Required - Name of the resource to add custom contents to.
- **contents** (Mapping[str, str]) - Optional - Custom dict to write for the named resource.
```

--------------------------------

### Set GITHUB_TOKEN environment variable

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Configures the GitHub token required for release automation using the gh CLI.

```bash
export GITHUB_TOKEN=$(gh auth token)
```

--------------------------------

### Implement tests for the workload module

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Tests the workload module directly by patching external dependencies like apt, subprocess, and os.kill.

```python
# tests/unit/test_myworkload.py
import signal

import pytest

from charm import myworkload


def test_install_calls_apt(monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        'charm.myworkload.apt.update',
        lambda: calls.append(('update', '')),
    )
    monkeypatch.setattr(
        'charm.myworkload.apt.add_package',
        lambda name, version: calls.append((name, version)),
    )
    myworkload.install()
    assert calls == [('update', ''), ('tinyproxy-bin', '1.11.1-3')]


def test_reload_config_sends_sigusr1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    pid_file = tmp_path / 'myworkload.pid'
    pid_file.write_text('1234')
    monkeypatch.setattr('charm.myworkload.PID_FILE', pid_file)

    sent: list[tuple[int, int]] = []
    monkeypatch.setattr('os.kill', lambda pid, sig: sent.append((pid, sig)))

    myworkload.reload_config()
    assert sent == [(1234, signal.SIGUSR1)]


def test_start_runs_subprocess(monkeypatch: pytest.MonkeyPatch):
    commands: list[list[str]] = []
    monkeypatch.setattr(
        'subprocess.run',
        lambda cmd, **kwargs: commands.append(cmd) or None,
    )
    myworkload.start()
    assert commands == [['myworkload']]
```

--------------------------------

### Client.get_changes(select, service)

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Retrieves a list of changes filtered by state and optionally by service name.

```APIDOC
## Client.get_changes(select, service)

### Description
Returns a list of changes based on the provided state filter.

### Parameters
- **select** (ChangeState) - Optional - The state to filter by (default: IN_PROGRESS).
- **service** (str) - Optional - The service name to filter by.

### Returns
- **list[Change]** - A list of matching change objects.
```

--------------------------------

### Add database integration test

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Verify that the charm reaches an active status after integrating with a deployed PostgreSQL application.

```python
@pytest.mark.juju_setup
def test_database_integration(charm: pathlib.Path, juju: jubilant.Juju):
    """Verify that the charm integrates with the database.

    Assert that the charm is active if the integration is established.
    """
    juju.deploy("postgresql-k8s", channel="14/stable", trust=True)
    juju.integrate(APP_NAME, "postgresql-k8s")
    juju.wait(jubilant.all_active)
```

--------------------------------

### Verify workload version in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-workload-version.md

Use the testing context to mock container execution and assert the workload version is correctly set.

```python
from ops import testing


def test_workload_version_is_set():
    ctx = testing.Context(MyCharm)
    # Suppose that the charm gets the workload version by running the command
    # `/bin/server --version` in the container. Firstly, we mock that out:
    container = testing.Container(
        'webserver',
        execs={testing.Exec(['/bin/server', '--version'], stdout='1.2\n')},
    )
    out = ctx.run(ctx.on.start(), testing.State(containers={container}))
    assert out.workload_version == '1.2'
```

--------------------------------

### get_container_pebble_plan(container_name: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Retrieves the current Pebble plan for a container.

```APIDOC
## get_container_pebble_plan(container_name: str)

### Description
Return the current plan that Pebble is executing for the given container.

### Parameters
- **container_name** (str) - Required - The simple name of the associated container.

### Returns
- **Plan** - The Pebble plan for this container.
```

--------------------------------

### ops.hookcmds.app_version_set

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Specifies the version of the application deployed.

```APIDOC
## ops.hookcmds.app_version_set(version: str)

### Description
Specify which version of the application is deployed.

### Parameters
- **version** (str) - Required - The version of the application software the unit is running.
```

--------------------------------

### Sync local changes

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Automatically push local file changes to remote charm units.

```shell
jhack sync myapp/0 --source ./src --source ./lib
```

--------------------------------

### Retrieve snap version

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Helper method to return the current snap channel.

```python
def _get_microsample_version(self):
    microsample_snap = snap.SnapCache()['microsample']
    return microsample_snap.channel
```

--------------------------------

### Simulate storage attachment events

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Use the storage_attached event to simulate the provisioning of requested storage volumes in a test suite.

```python
ctx = testing.Context(MyCharm)
foo_0 = testing.Storage('foo')
# The charm is notified that one of the storage volumes it has requested is ready:
ctx.run(ctx.on.storage_attached(foo_0), testing.State(storages={foo_0}))

foo_1 = testing.Storage('foo')
# The charm is notified that the other storage is also ready:
ctx.run(ctx.on.storage_attached(foo_1), testing.State(storages={foo_0, foo_1}))
```

--------------------------------

### Define an action parameter class

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/expose-operational-tasks-via-actions.md

Use a dataclass to define the structure of action parameters, enabling IDE hints and static type checking.

```python
@dataclasses.dataclass(frozen=True, kw_only=True)
class GetDbInfoAction:
    """Fetches database authentication information."""

    show_password: bool
    """Show username and password in output information."""
```

--------------------------------

### Implement Pebble identity management in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Retrieve secret contents and update Pebble identities using the ops library and passlib for password hashing.

```python
from passlib.hash import sha512_crypt


class MyCharm(ops.CharmBase):
    ...

    def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
        # The user must have:
        # - Created a secret with keys 'username' and 'password'
        # - Stored the secret ID in the 'metrics-secret-id' configuration option
        if not self.config.get('metrics-secret-id'):
            return
        secret_id = str(self.config['metrics-secret-id'])
        secret = self.model.get_secret(id=secret_id)
        content = secret.get_content()
        self._replace_identities(content['username'], content['password'])

    def _on_secret_changed(self, event: ops.SecretChangedEvent) -> None:
        if not self.config.get('metrics-secret-id'):
            return
        if event.secret.id == self.config['metrics-secret-id']:
            content = event.secret.peek_content()
            self._replace_identities(content['username'], content['password'])

    def _replace_identities(self, username: str, password: str) -> None:
        identities = {
            username: ops.pebble.Identity(
                access='metrics',
                basic=ops.pebble.BasicIdentity(
                    password=sha512_crypt.hash(password)
                ),
            ),
        }
        self.container.pebble.replace_identities(identities)
        logger.debug('New metrics username: %s', username)

    ...
```

--------------------------------

### Fetch resources in charm code

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-resources.md

Use Model.resources.fetch to retrieve the path to a declared resource, handling potential errors if the resource is missing.

```python
# ...
import logging
import ops

# ...
logger = logging.getLogger(__name__)


def _on_config_changed(self, event):
    # Get the path to the file resource named 'my-resource'
    try:
        resource_path = self.model.resources.fetch('my-resource')
    except ops.ModelError as e:
        self.unit.status = ops.BlockedStatus(
            "Something went wrong when claiming resource 'my-resource; "
            "run `juju debug-log` for more info'"
        )
        # might actually be worth it to just reraise this exception and let the charm error out;
        # depends on whether we can recover from this.
        logger.error(e)
        return
    except NameError as e:
        self.unit.status = ops.BlockedStatus(
            "Resource 'my-resource' not found; did you forget to declare it in charmcraft.yaml?"
        )
        logger.error(e)
        return

    # Open the file and read it
    with open(resource_path, 'r') as f:
        content = f.read()
    # do something
```

--------------------------------

### Configure service auto-restart

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Define restart policies and backoff parameters within the service layer configuration.

```yaml
services:
    server:
        override: replace
        command: python3 app.py

        # auto-restart options (showing defaults)
        on-success: restart   # can also be "shutdown" or "ignore"
        on-failure: restart   # can also be "shutdown" or "ignore"
        backoff-delay: 500ms
        backoff-factor: 2.0
        backoff-limit: 30s
```

--------------------------------

### Integration Testing Charm Actions

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Execute actions in an integration environment using the Juju client and verify the returned results.

```python
import pathlib

import jubilant


def test_snapshot_action(charm: pathlib.Path, juju: jubilant.Juju):
    task = juju.run(
        'your-app/0', 'snapshot', {'filename': 'db-snapshot.tar.gz'}
    )
    assert action.results['snapshot-size'].isdigit()
```

--------------------------------

### Set Cloud Specification in Harness

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Configures the cloud metadata for the harness before initializing the charm. Must be called before model.get_cloud_spec().

```python
# charm.py
class MyVMCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)

    def _on_start(self, event: ops.StartEvent):
        self.cloud_spec = self.model.get_cloud_spec()

# test_charm.py
def test_start(harness):
    cloud_spec = ops.model.CloudSpec.from_dict({
        'name': 'localhost',
        'type': 'lxd',
        'endpoint': 'https://127.0.0.1:8443',
        'credential': {
            'auth-type': 'certificate',
            'attrs': {
                'client-cert': 'foo',
                'client-key': 'bar',
                'server-cert': 'baz'
            },
        },
    })
    harness.set_cloud_spec(cloud_spec)
    harness.begin()
    harness.charm.on.start.emit()
    assert harness.charm.cloud_spec == cloud_spec
```

--------------------------------

### Execute specific unit test

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Command to run a specific test case using tox.

```text
tox -e unit -- -k test_version
```

--------------------------------

### Observe library events in a charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Use the library-provided events to manage relations within the charm's lifecycle.

```python
import ops
from charms.charm_with_lib.v0.database_lib import (
    DatabaseReadyEvent,
    DatabaseRequirer,
)


class MyCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.database = DatabaseRequirer(self, 'db-relation')
        framework.observe(self.database.on.ready, self._on_db_ready)

    def _on_db_ready(self, event: DatabaseReadyEvent):
        secret_content = event.credential_secret.get_content()
        ...
```

--------------------------------

### Integrate charm with COS Lite

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Connects the application model to the observability endpoints offered in the cos-lite model.

```text
juju switch testing
juju integrate fastapi-demo admin/cos-lite.grafana
juju integrate fastapi-demo admin/cos-lite.loki
juju integrate fastapi-demo admin/cos-lite.prometheus
```

--------------------------------

### Test charm configuration changes

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Verifies that the charm correctly processes valid configuration updates.

```python
def test_config_changed(tinyproxy_configured: MockTinyproxy):
    """Test that the charm correctly handles the config-changed event."""
    ctx = testing.Context(TinyproxyCharm)
    state_in = testing.State(config={"slug": "foo"})
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status == testing.ActiveStatus()
    assert tinyproxy_configured.is_running()
    assert tinyproxy_configured.config == (PORT, "foo")
    assert tinyproxy_configured.reloaded_config
```

--------------------------------

### Configure interface.yaml for local testing

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Specify the repository URL and branch for a requirer interface to ensure local test runs use the correct code version.

```yaml
requirers:
  - name: my-fancy-database-operator
    url: https://my-fancy-database-operator-repo
    branch: branch-with-my-conftest-changes
```

--------------------------------

### Specify charm path for deployment

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Override the default charm file path during integration testing.

```text
CHARM_PATH=/path/to/foo.charm tox -e integration
```

--------------------------------

### Verify Juju bootstrap

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/set-up-your-development-environment.md

Confirmation message indicating Juju has been successfully bootstrapped.

```text
msg="Bootstrapped Juju" provider=k8s
```

--------------------------------

### pebble_notify(container_name, key, *, data=None, repeat_after=None, type=NoticeType.CUSTOM)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Record a Pebble notice with the specified key and data.

```APIDOC
## pebble_notify

### Description
Record a Pebble notice with the specified key and data. If begin() has been called, this will trigger a notice event.

### Parameters
- **container_name** (str) - Required - Name of workload container.
- **key** (str) - Required - Notice key; must be in “example.com/path” format.
- **data** (dict[str, str]) - Optional - Data fields for this notice.
- **repeat_after** (timedelta) - Optional - Only allow this notice to repeat after this duration has elapsed.
- **type** (NoticeType) - Optional - Notice type (currently only “custom” notices are supported).

### Returns
- **str** - The notice’s ID.
```

--------------------------------

### Run commands in the container

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Execute one-off commands inside the container to inspect files or environment variables.

```shell
/charm/bin/pebble exec -- ls /etc/myapp/
/charm/bin/pebble exec --context myworkload -- env  # inherit the service's environment
```

--------------------------------

### Test status reporting with Context

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Uses the Context API to simulate update-status events and verify unit status transitions in isolation.

```python
from ops import pebble, testing

from charm import DemoCharm

layer = pebble.Layer({
    'services': {
        'workload': {
            'override': 'replace',
            'command': 'mock-command',
            'startup': 'enabled',
        },
    },
})


def test_status_active():
    ctx = testing.Context(DemoCharm)
    container = testing.Container(
        'my-container',
        layers={'base': layer},
        service_statuses={'workload': pebble.ServiceStatus.ACTIVE},
        can_connect=True,
    )
    state_in = testing.State(containers={container})
    state_out = ctx.run(ctx.on.update_status(), state_in)
    assert state_out.unit_status == testing.ActiveStatus()


def test_status_container_down():
    ctx = testing.Context(DemoCharm)
    container = testing.Container('my-container', can_connect=False)
    state_in = testing.State(containers={container})
    state_out = ctx.run(ctx.on.update_status(), state_in)
    assert state_out.unit_status == testing.MaintenanceStatus(
        'waiting for container'
    )
```

--------------------------------

### ops.hookcmds.action_log

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Records a progress message for the current action.

```APIDOC
## ops.hookcmds.action_log(message: str)

### Description
Record a progress message for the current action.

### Parameters
- **message** (str) - Required - The progress message to provide to the Juju user.
```

--------------------------------

### Add charm-libs to charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Define the required data_interfaces library dependency in the charmcraft.yaml file.

```yaml
charm-libs:
  - lib: data_platform_libs.data_interfaces
    version: "0"
```

--------------------------------

### Add Snap dependency to pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/run-workloads-with-a-charm-machines.md

Include the charmlibs-snap library in your project dependencies.

```toml
dependencies = [
    "charmlibs-snap>=1,<2",
    # ...
]
```

--------------------------------

### Deploy COS Lite and integrate with Loki

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Test functions to deploy the COS Lite bundle and establish integration between the application and Loki.

```python
@pytest.mark.juju_setup
def test_deploy_cos(charm: pathlib.Path, cos: jubilant.Juju):
    """Deploy COS Lite in a separate model."""
    cos.deploy("cos-lite", trust=True)
    cos.wait(jubilant.all_active, timeout=10 * 60)  # Allow time for the bundle to deploy.


@pytest.mark.juju_setup
def test_integrate_loki(charm: pathlib.Path, juju: jubilant.Juju, cos: jubilant.Juju):
    """Integrate our app with Loki from COS Lite."""
    cos.offer("loki", endpoint="logging")
    juju.integrate(APP_NAME, f"{cos.model}.loki")
    juju.wait(jubilant.all_active)
    cos.wait(jubilant.all_active)
```

--------------------------------

### Unit Testing StoredState

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Use the testing context to verify state persistence by inspecting stored state content or providing initial state mocks.

```python
def test_charm_sets_stored_state():
    ctx = testing.Context(MyCharm)
    state_in = testing.State()
    state_out = ctx.run(ctx.on.start(), state_in)
    ss = state_out.get_stored_state('_stored', owner_path='MyCharm')
    assert ss.content['expensive_value'] == 42


def test_charm_logs_stored_state():
    ctx = testing.Context(MyCharm)
    state_in = testing.State(
        stored_states={
            testing.StoredState(
                '_stored',
                owner_path='MyCharm',
                content={
                    'expensive_value': 42,
                },
            )
        }
    )
    state_out = ctx.run(ctx.on.install(), state_in)
    assert ctx.juju_log[0].message == 'Current value: 42'
```

--------------------------------

### Initialize Google Tag Manager

Source: https://github.com/canonical/operator/blob/main/docs/_templates/header.html

Initializes the Google Tag Manager script for tracking. Requires the GTM container ID to be passed as the final argument.

```javascript
(function(w, d, s, l, i) { w[l] = w[l] || []; w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' }); var f = d.getElementsByTagName(s)[0]; var j = d.createElement(s); var dl = ''; if (l != 'dataLayer') { dl = '&l=' + l; } j.async = true; j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl; f.parentNode.insertBefore(j, f); })(window, document, 'script', 'dataLayer', 'GTM-KNX3CJC');
```

--------------------------------

### Write to database via API

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Post data to the application endpoint to verify database write operations.

```text
curl -X 'POST' \
  'http://10.1.157.90:8000/addname/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'name=maksim'
```

--------------------------------

### Update _replan_workload method

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Updates the workload replan logic to include environment variables when adding the Pebble layer.

```python
def _replan_workload(self) -> None:
    """Define and start a workload using the Pebble API.

    You'll need to specify the right entrypoint and environment
    configuration for your specific workload. Tip: you can see the
    standard entrypoint of an existing container using docker inspect
    Learn more about interacting with Pebble at
        https://canonical.com/juju/docs/ops/latest/reference/pebble/
    Learn more about Pebble layers at
        https://ubuntu.com/docs/pebble/how-to/use-layers/
    """
    # Learn more about statuses at
    # https://documentation.ubuntu.com/juju/3.6/reference/status/
    self.unit.status = ops.MaintenanceStatus("Assembling Pebble layers")
    try:
        config = self.load_config(FastAPIConfig)
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        return
    env = self.get_app_environment()
    try:
        self.container.add_layer(
            "fastapi_demo",
            self._get_pebble_layer(config.server_port, env),
            combine=True,
        )
        logger.info("Added updated layer 'fastapi_demo' to Pebble plan")

        # Tell Pebble to incorporate the changes, including restarting the
        # service if required.
        self.container.replan()
        logger.info(f"Replanned with '{self.pebble_service_name}' service")
    except (ops.pebble.APIError, ops.pebble.ConnectionError) as e:
        logger.info("Unable to connect to Pebble: %s", e)
        return
    version = fastapi_demo.get_version(config.server_port)
    self.unit.set_workload_version(version)
```

--------------------------------

### Validate configuration in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Use the ops testing Context to trigger config-changed events and verify the resulting unit status.

```python
from ops import testing


def test_short_wiki_name():
    ctx = testing.Context(MyCharm)

    state_out = ctx.run(
        ctx.on.config_changed(), testing.State(config={'name': 'ww'})
    )

    assert isinstance(state_out.unit_status, testing.BlockedStatus)
```

--------------------------------

### Retrieve storage instance paths

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Access the list of storage instance locations provided by the model within an event handler.

```python
def _update_configuration(self, event: ops.EventBase):
    """Update the workload configuration."""
    cache = self.model.storages['cache']
    if not cache:
        logger.info("No instances available for storage 'cache'.")
        return
    cache_paths = [instance.location for instance in cache]
    # Configure the workload to use the storage instance paths.
    ...
```

--------------------------------

### ops.hookcmds.juju_reboot

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Reboot the host machine.

```APIDOC
## ops.hookcmds.juju_reboot(*, now: bool = False)

### Description
Reboot the host machine.

### Parameters
- **now** (bool) - Optional - Reboot immediately, killing the invoking process.
```

--------------------------------

### Define a DemoCharm class

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

A sample charm class that manages a database relation and provides an action to retrieve the endpoint.

```python
class DemoCharm(ops.CharmBase):
    """Manage the workload."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        # Use database helpers from charms.data_platform_libs.v0.data_interfaces.
        self.database = DatabaseRequires(
            self, relation_name='database', database_name='my-db'
        )
        framework.observe(
            self.database.on.database_created, self._on_database_available
        )
        framework.observe(
            self.database.on.endpoints_changed, self._on_database_available
        )
        framework.observe(
            self.on['get-db-endpoint'].action, self._on_get_db_endpoint_action
        )

    def _on_database_available(
        self, _: DatabaseCreatedEvent | DatabaseEndpointsChangedEvent
    ) -> None:
        """When a database endpoint becomes available or changes, reconfigure the workload."""
        endpoint = self.get_endpoint_from_relation()
        if endpoint:
            self.write_workload_config(endpoint)
            ...  # Ask the workload to reload configuration.

    def _on_get_db_endpoint_action(self, event: ops.ActionEvent) -> None:
        """Handle the get-db-endpoint action."""
        endpoint = self.get_endpoint_from_relation()
        if endpoint:
            event.set_results({'endpoint': endpoint})
        else:
            event.fail('Database endpoint is not available')

    def get_endpoint_from_relation(self) -> str | None:
        """Get the database endpoint from the relation data."""
        relations = self.database.fetch_relation_data()
        for data in relations.values():
            if data:
                return data['endpoints']

    def write_workload_config(self, config: str) -> None:
        """Update the workload's configuration."""
        ...  # Write a config file. Or in a K8s charm, use Pebble to push config to the container.
```

--------------------------------

### Passing patched charm to Context

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Initialize the testing Context using the patched charm fixture.

```python
def test_charm_runs(my_charm):
    # Arrange:
    #  Create a Context to specify what code we will be running
    ctx = testing.Context(my_charm)
    # ...
```

--------------------------------

### Integration test with upstream-source

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-resources.md

Deploy a charm in integration tests by mapping resources to their upstream-source defined in metadata.

```python
import pathlib

import jubilant
import pytest
import yaml


METADATA = yaml.safe_load(pathlib.Path('./charmcraft.yaml').read_text())


@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    resources = {
        name: res['upstream-source']
        for name, res in METADATA['resources'].items()
    }
    juju.deploy(charm, resources=resources)
    juju.wait(jubilant.all_active)
```

--------------------------------

### Limit log output

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Fetch a specific number of lines and exit immediately, useful for scripting.

```shell
juju debug-log --limit 100
```

--------------------------------

### Define database event handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Implement the method to handle database events and trigger workload replanning.

```python
def _on_database_endpoint(
    self, _: DatabaseCreatedEvent | DatabaseEndpointsChangedEvent
) -> None:
    """Event is fired when the database is created or its endpoint is changed."""
    self._replan_workload()
```

--------------------------------

### Guard against Pebble connection issues

Source: https://github.com/canonical/operator/blob/main/docs/explanation/storedstate-guidance.md

Use this pattern to handle cases where a container might not be running, avoiding reliance on cached state from events.

```python
def some_event_handler(event):
    try:
        self.do_thing_that_assumes_container_running()
    except ops.pebble.ConnectionError:
        event.defer()
        return
```

--------------------------------

### update_config(key_values: Mapping[str, str | int | float | bool] | None = None, unset: Iterable[str] = ())

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Updates the charm configuration and triggers a config_changed event.

```APIDOC
## update_config(key_values: Mapping[str, str | int | float | bool] | None = None, unset: Iterable[str] = ())

### Description
Update the config as seen by the charm. This will trigger a config_changed event.

### Parameters
- **key_values** (Mapping) - Optional - A Mapping of key:value pairs to update in config.
- **unset** (Iterable[str]) - Optional - An iterable of keys to remove from config.

### Raises
- **ValueError** - if the key is not present in the config.
```

--------------------------------

### Trigger events manually

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Simulate specific events on a live unit to test event handlers.

```shell
jhack fire myapp/0 update-status
jhack fire myapp/0 config-changed
```

--------------------------------

### Set charm version via git hash

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-charm-version.md

Manually generate a version file containing the current git commit hash.

```shell
$ git rev-parse HEAD > version
$ ls
lib      src    tox.ini charmcraft.yaml  LICENSE  requirements.txt  tests  version
$ cat version
0522e1fd009dac78adb3d0652d91a1e8ff7982ae
```

--------------------------------

### restart_services

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Restarts a list of services and waits for them to reach the running state.

```APIDOC
## restart_services(services: Iterable[str], timeout: float = 30.0, delay: float = 0.1) -> ChangeID

### Description
Restarts the specified services. If a service is running, it is stopped and restarted; if it is stopped, it is started.

### Parameters
- **services** (Iterable[str]) - Required - Non-empty list of service names to restart.
- **timeout** (float) - Optional - Seconds to wait for the restart to complete. If 0, returns immediately without waiting.
- **delay** (float) - Optional - Seconds to wait before executing the restart.

### Returns
- **ChangeID** - The ID of the restart change operation.

### Raises
- **ChangeError** - Raised if services fail to transition and timeout is non-zero.
```

--------------------------------

### Verify open ports in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-opened-ports.md

Use ops.testing.State.opened_ports to assert the expected state of open ports after an event execution.

```python
def test_open_port():
    ctx = testing.Context(MyCharm)
    state_in = testing.State()
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.opened_ports == {testing.TCPPort(8000)}
```

--------------------------------

### Write a file to the workload container

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use write_text to write content to a file or ensure_contents to conditionally update a file based on ownership and permissions.

```python
config = '...'
(self.myapp_root / 'config.yaml').write_text(config)
```

```python
changed = pathops.ensure_contents(self.myapp_root / 'config.yaml', config)
```

--------------------------------

### ops.hookcmds.state_set(data: Mapping[str, str])

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Sets server-side-state values.

```APIDOC
## ops.hookcmds.state_set(data: Mapping[str, str])

### Description
Set server-side-state values.

### Parameters
- **data** (Mapping[str, str]) - Required - The key-value pairs to set in the server-side state.
```

--------------------------------

### Define integration dependencies in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Specifies the required integration testing packages within the dependency groups of pyproject.toml.

```toml
[dependency-groups]
...
integration = [
    "jubilant>=1.8,<2",
    "pytest-jubilant>=2,<3",
]
```

--------------------------------

### Unit test charm resources

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-resources.md

Inject resources into the testing context using testing.Resource to verify resource fetching logic.

```python
import pathlib

from ops import testing

ctx = testing.Context(
    MyCharm, meta={'name': 'julie', 'resources': {'foo': {'type': 'oci-image'}}}
)
resource = testing.Resource(name='foo', path='/path/to/resource.tar')
with ctx(ctx.on.start(), testing.State(resources={resource})) as mgr:
    path = mgr.charm.model.resources.fetch('foo')
    assert path == pathlib.Path('/path/to/resource.tar')
```

--------------------------------

### Log events in charm methods

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Replace legacy juju-log calls with standard Python logging.

```python
def _on_website_relation_departed(self, _event):  # noqa
    logger.debug('%s departed website relation', self.unit.name)
```

--------------------------------

### Implement config-changed event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Define the event handler method to process configuration changes within the charm.

```python
def _on_config_changed(self, event: ops.ConfigChangedEvent):
    name = self.typed_config.name
    existing_name = self.get_wiki_name()
    if name == existing_name:
        # Nothing to do.
        return
    logger.info('Changing wiki name to %s', name)
    self.set_wiki_name(name)
```

--------------------------------

### Observe storage-attached event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Register an event handler for the storage-attached event within the charm's __init__ method.

```python
framework.observe(self.on['cache'].storage_attached, self._update_configuration)
```

--------------------------------

### Observe stop and remove events

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Register event handlers for stop and remove lifecycle events within the charm's __init__ method.

```python
        framework.observe(self.on.stop, self._on_stop)
        framework.observe(self.on.remove, self._on_remove)
```

--------------------------------

### Declare tracing relations in metadata.yaml

Source: https://github.com/canonical/operator/blob/main/docs/explanation/tracing.md

Use this configuration to define the required tracing and certificate transfer interfaces for a charm.

```yaml
requires:
  charm-tracing:
    interface: tracing
    limit: 1
    optional: true
  receive-ca-cert:
    interface: certificate_transfer
    limit: 1
    optional: true
```

--------------------------------

### Run Juju CLI commands

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Uses the Juju CLI escape hatch to execute commands within the Juju context.

```python
...
command = ['add-credential', 'some-cloud', '-f', 'your-creds-file.yaml']
stdout = juju.cli(*command)
...
command = ['unexpose', 'some-application']
stdout = juju.cli(*command, include_model=True)
...
```

--------------------------------

### Google-style Docstring Format

Source: https://github.com/canonical/operator/blob/main/AGENTS.md

Use Google-style docstrings for public APIs to ensure proper Sphinx reference documentation generation.

```python
def my_function(param: str, count: int = 1) -> list[str]:
    """Brief one-line summary.

    Longer description providing more context. Focus on what the function
    does for users, not implementation details.

    Args:
        param: Description of the parameter.
        count: Number of times to repeat. Defaults to 1.

    Returns:
        A list of processed strings.

    Raises:
        ValueError: If count is negative.

    Example:
        >>> my_function("hello", 2)
        ['hello', 'hello']
    """
```

--------------------------------

### Migrate Wait for Condition

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Use juju.wait with ready and error callables to replace model.wait_for_idle.

```python
# pytest-operator
async def test_active(model: Model):
    await model.deploy('mycharm')
    await model.wait_for_idle(status='active')  # implies raise_on_error=True


# jubilant
def test_active(juju: jubilant.Juju):
    juju.deploy('mycharm')
    juju.wait(jubilant.all_active, error=jubilant.any_error)
```

--------------------------------

### Verify open ports in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-opened-ports.md

Perform network connection checks against the unit's public address to validate port accessibility.

```python
def is_port_open(host: str, port: int) -> bool:
    """Check if a port is opened in a particular host."""
    try:
        with socket.create_connection((host, port), timeout=5):
            return True  # If connection succeeds, the port is open
    except (ConnectionRefusedError, TimeoutError):
        return False  # If connection fails, the port is closed


def test_open_ports(juju: jubilant.Juju):
    """Verify that setting the server-port in the charm's opens that port.

    Assert blocked status in case of port 22 and active status for others.
    """
    # Get the public address of the app:
    address = juju.status().apps['your-app'].units['your-app/0'].public_address
    # Validate that initial port is opened:
    assert is_port_open(address, 8000)

    # Set the port to 22 and validate the app goes to blocked status with the port not opened:
    juju.config('your-app', {'server-port': '22'})
    juju.wait(jubilant.all_blocked)
    assert not is_port_open(address, 22)

    # Set the port to 6789 and validate the app goes to active status with the port opened.
    juju.config('your-app', {'server-port': '6789'})
    juju.wait(jubuilant.all_active)
    assert is_port_open(address, 6789)
```

--------------------------------

### Verify Ops version in a deployed unit

Source: https://github.com/canonical/operator/blob/main/docs/explanation/security.md

Use this command to check the currently running version of the ops library within a specific Juju unit.

```text
juju exec --unit <unit> -- bash -c '/var/lib/juju/agents/unit-*/charm/venv/bin/python -c "import ops; print(ops.__version__)"'
```

--------------------------------

### Use CLI fallback

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Executes arbitrary Juju commands via juju.cli, which raises a CLIError on non-zero exit codes.

```python
# pytest-operator
return_code, _, scp_err = await ops_test.juju(
    'scp',
    '--container',
    'postgresql',
    './testing_database/testing_database.sql',
    f'{postgres_app.units[0].name}:.',
)
assert return_code == 0, scp_err

# jubilant
juju.cli(
    'scp',
    '--container',
    'postgresql',
    './testing_database/testing_database.sql',
    'postgresql-k8s/0:.',
)
```

--------------------------------

### List files in a directory

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Iterate over directory contents using standard path manipulation methods.

```python
paths = list(self.myapp_root.iterdir())
for yaml_path in self.myapp_root.glob('*.yaml'):
    # ...
```

--------------------------------

### Define fast_forward context manager

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

A custom implementation of the fast_forward context manager for migrating existing tests that require accelerated update-status hooks.

```python
@contextlib.contextmanager
def fast_forward(juju: jubilant.Juju):
    """Context manager that temporarily speeds up update-status hooks to fire every 10s."""
    old = juju.model_config()['update-status-hook-interval']
    juju.model_config({'update-status-hook-interval': '10s'})
    try:
        yield
    finally:
        juju.model_config({'update-status-hook-interval': old})
```

--------------------------------

### Test an action failure using state-transition

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Verifies that an action correctly triggers an ActionFailed exception when expected.

```python
import pytest
from ops import testing

from charm import DemoCharm


def test_get_value_action_failed():
    ctx = testing.Context(DemoCharm)
    state_in = testing.State()
    with pytest.raises(testing.ActionFailed) as exc_info:
        ctx.run(
            ctx.on.action('get-value', params={'value': 'please fail'}),
            state_in,
        )
    assert exc_info.value.message == 'Action failed, as requested'
```

--------------------------------

### ops.pebble.Client.add_layer

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Dynamically add a new layer onto the Pebble configuration layers.

```APIDOC
## add_layer(label: str, layer: str | LayerDict | Layer, *, combine: bool = False)

### Description
Dynamically add a new layer onto the Pebble configuration layers.

### Parameters
- **label** (str) - Required - The label for the layer.
- **layer** (str | LayerDict | Layer) - Required - The layer definition.
- **combine** (bool) - Optional - If true, combines with existing layer if label matches.
```

--------------------------------

### Test output logs

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Expected output logs for the integration tests.

```text
tests/integration/test_charm.py::test_deploy
...
INFO     jubilant.wait:_juju.py:1164 wait: status changed:
- .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.current = 'executing'
- .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.message = 'running start hook'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.current = 'idle'
PASSED
```

```text
tests/integration/test_charm.py::test_workload_version_is_set
...
INFO     jubilant.wait:_juju.py:1491 wait: status changed:
- .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.current = 'executing'
- .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.message = 'running demo-server-pebble-ready hook'
+ .apps['fastapi-demo'].units['fastapi-demo/0'].juju_status.current = 'idle'
+ .apps['fastapi-demo'].version = '2.1.0'
PASSED
```

```text
tests/integration/test_charm.py::test_database_integration
...
INFO     jubilant.wait:_juju.py:1164 wait: status changed:
- .apps['postgresql-k8s'].app_status.current = 'waiting'
- .apps['postgresql-k8s'].app_status.message = 'awaiting for cluster to start'
+ .apps['postgresql-k8s'].app_status.current = 'active'
+ .apps['postgresql-k8s'].app_status.message = 'Primary'
- .apps['postgresql-k8s'].units['postgresql-k8s/0'].workload_status.current = 'waiting'
- .apps['postgresql-k8s'].units['postgresql-k8s/0'].workload_status.message = 'awaiting for cluster to start'
+ .apps['postgresql-k8s'].units['postgresql-k8s/0'].workload_status.current = 'active'
+ .apps['postgresql-k8s'].units['postgresql-k8s/0'].workload_status.message = 'Primary'
PASSED
```

--------------------------------

### Define relation endpoint in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Configure the charm to require a database relation using the postgresql_client interface.

```yaml
requires:
  database:
    interface: postgresql_client
    limit: 1
    optional: false
```

--------------------------------

### set_can_connect(container: str | Container, val: bool)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Changes the simulated connection status of a container.

```APIDOC
## set_can_connect(container: str | Container, val: bool)

### Description
Change the simulated connection status of a container’s underlying Pebble client.

### Parameters
- **container** (str | Container) - Required - The container to update.
- **val** (bool) - Required - The connection status to set.
```

--------------------------------

### Add binding name to Network objects

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Network objects are now added as a set and require a binding name during creation.

```python
# Older Scenario code
state = State(networks={'foo': Network.default()})

# Scenario 7.x
state = State(networks={Network.default('foo')})
```

--------------------------------

### ops.hookcmds.resource_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves the path to a locally cached resource file.

```APIDOC
## ops.hookcmds.resource_get(name: str)

### Description
Get the path to the locally cached resource file.

### Parameters
- **name** (str) - Required - The name of the resource.

### Response
- **Returns** (Path) - The path to the resource file.
```

--------------------------------

### set_model_info(name: str | None = None, uuid: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Sets the name and UUID of the model represented by the harness.

```APIDOC
## set_model_info(name: str | None = None, uuid: str | None = None)

### Description
Sets the name and UUID of the model that this is representing. This cannot be called after begin() has been invoked.

### Parameters
- **name** (str) - Optional - The name of the model.
- **uuid** (str) - Optional - The UUID of the model.
```

--------------------------------

### ops.pebble.Client.ack_warnings

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Acknowledge warnings up to a specified timestamp.

```APIDOC
## ack_warnings(timestamp: datetime) -> int

### Description
Acknowledge warnings up to given timestamp, return number acknowledged.

### Parameters
- **timestamp** (datetime) - Required - The timestamp up to which warnings should be acknowledged.
```

--------------------------------

### Client.get_identities()

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Retrieves all identities configured in Pebble.

```APIDOC
## Client.get_identities()

### Description
Returns a dictionary mapping identity names to identity objects.

### Returns
- **dict[str, Identity]** - Map of identity names to objects.
```

--------------------------------

### Advanced Wait Configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Configure polling delay, timeout, and success thresholds for juju.wait.

```python
juju.deploy('mycharm')
juju.wait(
    ready=lambda status: jubilant.all_active(status, 'mycharm'),
    error=jubilant.any_error,
    delay=0.2,  # poll "juju status" every 200ms (default 1s)
    timeout=60,  # set overall timeout to 60s (default juju.wait_timeout)
    successes=7,  # require ready to return success 7x in a row (default 3)
)
```

--------------------------------

### Retrieve unit IP address

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Use this command to find the IP address of the unit for the VS Code connection configuration.

```shell
juju show-unit myapp/0 | yq '.*.address'
```

--------------------------------

### Define Unit Test for Pebble Layer

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

This test verifies that the charm correctly configures the Pebble layer and sets the workload status upon receiving a pebble-ready event.

```python
import ops
import pytest
from ops import testing

from charm import FastAPIDemoCharm

# The default Pebble layer in the application image.
# Defined in https://github.com/canonical/api_demo_server/blob/master/rockcraft.yaml
ROCK_LAYER = ops.pebble.Layer(
    {
        "services": {
            "fastapi": {
                "override": "replace",
                "summary": "FastAPI demo server",
                "command": "/bin/uvicorn api_demo_server.app:app --host 0.0.0.0 --port 8000",
                "startup": "enabled",
                "environment": {"DEMO_SERVER_LOGFILE": "/tmp/demo_server.log"},
                "on-success": "shutdown",
                "on-failure": "shutdown",
            }
        },
    }
)


def mock_get_version(port: int):
    """Get a mock version string without executing the workload code."""
    return "0.0.1"


@pytest.fixture
def mock_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fastapi_demo.get_version", mock_get_version)


def test_pebble_layer(mock_version):
    ctx = testing.Context(FastAPIDemoCharm)
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        leader=True,
    )
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)
    # Expected plan after Pebble ready (our charm doesn't add any layers).
    expected_plan = ops.pebble.Plan(ROCK_LAYER.to_dict())

    # Check that we have the plan we expected:
    assert state_out.get_container(container.name).plan == expected_plan
    # Check the unit is active:
    assert state_out.unit_status == testing.ActiveStatus()
    # Check the service was started:
    assert (
        state_out.get_container(container.name).service_statuses["fastapi"]
        == ops.pebble.ServiceStatus.ACTIVE
    )
    # Check the workload version is set:
    assert state_out.workload_version == "0.0.1"
```

--------------------------------

### Read Pebble notices and warnings

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Commands to retrieve unacknowledged notices and system warnings.

```shell
pebble notices                # notices not yet acknowledged
pebble notice 4               # detail for one notice by ID
pebble warnings --all         # Pebble's own warnings (deprecations, config issues)
```

--------------------------------

### Configure VS Code for remote attachment

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Add this configuration to .vscode/launch.json to connect the VS Code debugger to the charm unit.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach to charm",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "<UNIT_IP>",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ],
            "justMyCode": true
        }
    ]
}
```

--------------------------------

### ops.hookcmds.status_set(status, message=None, *, app=False)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Sets the status of a unit or an application.

```APIDOC
## ops.hookcmds.status_set(status: Literal['active', 'blocked', 'maintenance', 'waiting'], message: str | None = None, *, app: bool = False)

### Description
Set a status of a unit or an application.

### Parameters
- **status** (Literal) - Required - The status to set.
- **message** (str | None) - Optional - A message to include in the status.
- **app** (bool) - Optional - If True, set this status for the application to which the unit belongs.
```

--------------------------------

### Unit test a relation event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Define a Relation object, include it in the State, and run the event using the Context runner.

```python
from ops import testing

ctx = testing.Context(MyCharm)
relation = testing.Relation(endpoint='smtp', remote_units_data={1: {}})
state_in = testing.State(relations={relation})
state_out = ctx.run(
    ctx.on.relation_joined(relation, remote_unit=1), state=state_in
)
assert (
    'smtp_credentials'
    in state_out.get_relation(relation.id).remote_units_data[1]
)
```

--------------------------------

### ops.hookcmds.credential_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Access cloud credentials.

```APIDOC
## ops.hookcmds.credential_get()

### Description
Access cloud credentials for the current unit.
```

--------------------------------

### Update _get_pebble_layer method

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Configures the Pebble layer to include environment variables within the service definition.

```python
def _get_pebble_layer(self, port: int, env: dict[str, str]) -> ops.pebble.Layer:
    """Pebble layer for the FastAPI demo services."""
    cmd = f"/bin/uvicorn api_demo_server.app:app --host 0.0.0.0 --port {port}"
    service: ops.pebble.ServiceDict = {
        "override": "merge",
        "command": cmd,
        "environment": env,
    }
    layer: ops.pebble.LayerDict = {
        "summary": "FastAPI demo service",
        "description": "pebble config layer for FastAPI demo server",
        "services": {self.pebble_service_name: service},
    }
    return ops.pebble.Layer(layer)
```

--------------------------------

### Test invalid configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Ensure the charm enters a blocked state when an invalid port is provided in the configuration.

```python
def test_config_changed_invalid_port(mock_version):
    ctx = testing.Context(FastAPIDemoCharm)
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        config={"server-port": 22},
        leader=True,
    )
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        "Invalid port number, 22 is reserved for SSH"
    )
```

--------------------------------

### Save Juju debug logs to disk

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Use the --juju-dump-logs option with tox to save logs to a specified directory.

```text
tox -e integration -- --juju-dump-logs logs
```

--------------------------------

### Define integration tests for a charm

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Use this code in tests/integration/test_charm.py to verify charm deployment and workload versioning. Requires pytest-jubilant and a properly configured charmcraft.yaml.

```python
import logging
import pathlib

import jubilant
import pytest
import yaml

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(pathlib.Path("charmcraft.yaml").read_text())
APP_NAME = METADATA["name"]


@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    """Deploy the charm under test."""
    resources = {
        "demo-server-image": METADATA["resources"]["demo-server-image"]["upstream-source"]
    }
    juju.deploy(charm, app=APP_NAME, resources=resources)
    juju.wait(jubilant.all_active)


def test_workload_version_is_set(charm: pathlib.Path, juju: jubilant.Juju):
    """Verify that the workload version has been set."""
    expected_version = "2.1.0"  # Hardcoded for simplicity.
    juju.wait(lambda status: status.apps[APP_NAME].version == expected_version)
```

--------------------------------

### Format log messages correctly

Source: https://github.com/canonical/operator/blob/main/docs/howto/log-from-your-charm.md

Pass arguments to the logger instead of manually formatting strings to ensure efficient log processing.

```python
# Do this!
logger.info("Got some information %s", info)
# Don't do this
logger.info("Got some information {}".format(info))
# Or this ...
logger.info(f"Got some more information {more_info}")
```

--------------------------------

### Test custom endpoint names

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Ensures that the library correctly respects and uses custom endpoint names provided during initialization.

```python
import pytest
import ops
from ops import testing
from lib.charms.my_charm.v0.my_lib import DatabaseReadyEvent, DatabaseRequirer


@pytest.fixture(params=['foo', 'bar'])
def endpoint(request):
    return request.param


@pytest.fixture
def my_charm_type(endpoint: str):
    class MyTestCharm(ops.CharmBase):
        # 'database' is declared as well as the custom endpoint, so that a
        # requirer that ignored the endpoint argument and hard-coded
        # 'database' would still construct -- the test then fails because no
        # DatabaseReadyEvent is emitted, rather than because the charm
        # couldn't observe a relation it never declared.
        META = {
            'name': 'my-charm',
            'requires': {
                endpoint: {'interface': 'my_interface'},
                'database': {'interface': 'my_interface'},
            },
        }

        def __init__(self, framework: ops.Framework):
            super().__init__(framework)
            self.db = DatabaseRequirer(self, endpoint=endpoint)

    return MyTestCharm


def test_custom_endpoint_name(my_charm_type, endpoint: str):
    """Verify that the requirer observes the caller-supplied endpoint."""
    ctx = testing.Context(my_charm_type, meta=my_charm_type.META)
    relation = testing.Relation(endpoint)
    secret = testing.Secret({'username': 'admin', 'password': 'admin'})
    state_in = testing.State(relations={relation}, secrets={secret})
    ctx.run(ctx.on.relation_changed(relation), state_in)
    assert any(
        isinstance(event, DatabaseReadyEvent) for event in ctx.emitted_events
    )
```

--------------------------------

### Declare a provides relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Defines a provider endpoint for external charm integration.

```yaml
provides:
  smtp:
    interface: smtp
```

--------------------------------

### ops.pebble.ExecProcess.wait_output

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Waits for the process to finish and returns the captured stdout and stderr.

```APIDOC
### wait_output() -> tuple[AnyStr, AnyStr | None]

Waits for the process to finish and returns a tuple containing (stdout, stderr). If combine_stderr was True, stdout will include the process's standard error, and stderr will be None.

#### Raises
- **ChangeError** - If there was an error starting or running the process.
- **ExecError** - If the process exits with a non-zero exit code.
- **TypeError** - If the exec call was made with the stdout argument.
```

--------------------------------

### Validate application connectivity

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Sends an HTTP request to the pod IP to verify the application is responding.

```default
curl 10.1.157.73:8000/version
```

```default
{"version":"2.1.0"}
```

--------------------------------

### Test invalid configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Set an invalid port number to trigger a blocked state and verify the status.

```text
juju config fastapi-demo server-port=22
juju status
```

--------------------------------

### Add testing dependency in pyproject.toml

Source: https://github.com/canonical/operator/blob/main/testing/README.md

Include the ops testing extra in your dependency groups to enable unit testing support.

```toml
[dependency-groups]
test = ['ops[testing]<4.0']
```

--------------------------------

### Initialize StoredState in a Charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Define a StoredState object within the charm class and set default values during initialization.

```python
class MyCharm(ops.CharmBase):
    _stored = ops.StoredState()

    def __init__(self, framework):
        super().__init__(framework)
        self._stored.set_default(expensive_value=None)
```

--------------------------------

### Test relation data handling

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Verifies that the charm correctly processes database relation data and updates the container environment variables.

```python
def test_relation_data(mock_version):
    ctx = testing.Context(FastAPIDemoCharm)
    relation = testing.Relation(
        endpoint="database",
        interface="postgresql_client",
        remote_app_name="postgresql-k8s",
        remote_app_data={
            "endpoints": "example.com:5432",
            "username": "foo",
            "password": "bar",
        },
    )
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        relations={relation},
        leader=True,
    )

    state_out = ctx.run(ctx.on.relation_changed(relation), state_in)

    assert state_out.get_container(container.name).plan.services["fastapi"].environment == {
        **ROCK_LAYER.services["fastapi"].environment,
        "DEMO_SERVER_DB_HOST": "example.com",
        "DEMO_SERVER_DB_PORT": "5432",
        "DEMO_SERVER_DB_USER": "foo",
        "DEMO_SERVER_DB_PASSWORD": "bar",
    }
```

--------------------------------

### Introspect Charm Instance during State Transition

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Use the Context object as a context manager to access the charm instance and perform assertions before and after the event execution.

```python
import pytest


class MyCharm(ops.CharmBase):
    msg = ''

    def __init__(self, framework):
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)

    def _on_start(self, _):
        if self.unit.is_leader():
            self.msg = 'I rule'
        else:
            self.msg = 'I am ruled'
        self.unit.status = ops.ActiveStatus(self.msg)


@pytest.mark.parametrize('leader', (True, False))
def test_status_leader(leader):
    ctx = testing.Context(MyCharm, meta={'name': 'foo'})
    with ctx(ctx.on.start(), testing.State(leader=leader)) as mgr:
        charm = mgr.charm
        assert charm.msg == ''
        assert charm.unit.status == testing.UnknownStatus()
        state_out = mgr.run()
    msg = 'I rule' if leader else 'I am ruled'
    assert charm.msg == msg
    assert charm.unit.status == testing.ActiveStatus(msg)
    assert state_out.unit_status == charm.unit.status
```

--------------------------------

### Delete files and directories

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Remove files, empty directories, or entire directory trees using path methods or container removal.

```python
(self.myapp_root / 'access.log').unlink()
```

```python
(self.myapp_root / 'cachedir').rmdir()
```

```python
self.container.remove_path('/etc/myapp/cachedir', recursive=True)
```

--------------------------------

### Observe storage-detaching event in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Register an observer for the storage-detaching event within the charm's __init__ method.

```python
framework.observe(
    self.on['cache'].storage_detaching, self._on_storage_detaching
)
```

--------------------------------

### Access environment variables via CharmBase

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Retrieve unit information directly from the CharmBase unit attribute instead of environment variables.

```python
JUJU_UNIT_NAME = os.environ['JUJU_UNIT_NAME']
```

--------------------------------

### Grant secret access

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Grant the charm access to the user secret after deployment.

```bash
juju grant-secret metrics-user-password <charm-name>
```

--------------------------------

### Declare a new relation

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Registers a relation with a remote application and optionally populates initial relation data.

```default
secret_id = harness.add_model_secret('mysql', {'password': 'SECRET'})
harness.add_relation('db', 'mysql', unit_data={
    'host': 'mysql.localhost,
    'username': 'appuser',
    'secret-id': secret_id,
})
```

--------------------------------

### Read remote file content

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Use the returned context manager to ensure the file is closed promptly and prevent memory leaks.

```default
with container.pull('/etc/config.yaml') as f:
    content = f.read()
```

--------------------------------

### Handle execution errors

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Catch ExecError to inspect exit codes and stderr when a command fails.

```python
process = container.exec(['cat', '--bad-arg'])
try:
    stdout, _ = process.wait_output()
    logger.info(stdout)
except ops.pebble.ExecError as e:
    logger.error('Exited with code %d. Stderr:', e.exit_code)
    for line in e.stderr.splitlines():
        logger.error('    %s', line)
```

--------------------------------

### Unit test a charm

Source: https://github.com/canonical/operator/blob/main/README.md

Uses ops.testing to simulate Juju events and verify the container plan and service status.

```python
import ops
from ops import testing

from charm import OpsExampleCharm


def test_httpbin_pebble_ready():
    # Arrange:
    ctx = testing.Context(OpsExampleCharm)
    container = testing.Container('httpbin', can_connect=True)
    state_in = testing.State(containers={container})

    # Act:
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)

    # Assert:
    updated_plan = state_out.get_container(container.name).plan
    expected_plan = {
        'services': {
            'httpbin': {
                'override': 'replace',
                'summary': 'httpbin',
                'command': 'gunicorn -b 0.0.0.0:80 httpbin:app -k gevent',
                'startup': 'enabled',
                'environment': {'GUNICORN_CMD_ARGS': '--log-level info'},
            }
        },
    }
    assert expected_plan == updated_plan
    assert (
        state_out.get_container(container.name).service_statuses['httpbin']
        == ops.pebble.ServiceStatus.ACTIVE
    )
    assert state_out.unit_status == testing.ActiveStatus()
```

--------------------------------

### Observe config-changed events

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-configuration.md

Register the config-changed event observer in the charm's __init__ method.

```python
self.framework.observe(self.on.config_changed, self._on_config_changed)
```

--------------------------------

### Access a machine charm unit via SSH

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Connect to a machine charm unit using the Juju CLI.

```shell
juju ssh myapp/0
```

--------------------------------

### ops.hookcmds.open_port

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Register a request to open a port or port range.

```APIDOC
## ops.hookcmds.open_port(protocol: str | None = None, port: int | None = None, *, to_port: int | None = None, endpoints: str | Iterable[str] | None = None)

### Description
Register a request to open a port or port range.

### Parameters
- **protocol** (str) - Optional - Open the port(s) for the specified protocol.
- **port** (int) - Optional - If to_port is not specified, open only this port.
- **to_port** (int) - Optional - Open a range of ports from port to to_port.
- **endpoints** (str | Iterable[str]) - Optional - Constrain the open request to specific endpoints.
```

--------------------------------

### Configure stored log levels

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Set the logging-config model setting to control which log levels are stored in the Juju database.

```shell
juju model-config logging-config="<root>=WARNING;unit=DEBUG"
```

--------------------------------

### Initial failing state-transition test

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

A test definition that fails because it does not provide the required container to the testing context.

```python
def test_get_value_action():
    ctx = testing.Context(DemoCharm)
    state_in = testing.State()
    ctx.run(ctx.on.action('get-value', params={'value': 'foo'}), state_in)
    assert ctx.action_results == {'out-value': 'foo'}
```

--------------------------------

### Import dependencies for integration tests

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Required imports for the integration test suite in tests/integration/test_charm.py.

```python
import json
import logging
import pathlib
import time
import urllib.error
import urllib.request

import jubilant
import pytest
import pytest_jubilant
import yaml
```

--------------------------------

### Configure PYTHONPATH for IDE

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Commands to set the PYTHONPATH environment variable to ensure the IDE resolves library imports correctly.

```bash
# in your project directory (~/k8s-tutorial), set
export PYTHONPATH=lib
# or update
export PYTHONPATH=lib:$PYTHONPATH
```

--------------------------------

### Handle website relation joined event

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Update relation databag contents using the relation helper.

```python
def _on_website_relation_joined(self, _event):
    relation = self._get_website_relation()
    relation.data[self.unit].update({
        'hostname': self.private_address,
        'port': self.port,
    })
```

--------------------------------

### Stream I/O to a process

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Perform streaming I/O by writing to stdin and reading from stdout attributes of the ExecProcess instance.

```python
process = container.exec(['cat'])


# Thread that sends data to process's stdin
def stdin_thread():
    try:
        for line in ['one\n', '2\n', 'THREE\n']:
            process.stdin.write(line)
            process.stdin.flush()
            time.sleep(1)
    finally:
        process.stdin.close()


threading.Thread(target=stdin_thread).start()

# Log from stdout stream as output is received
for line in process.stdout:
    logging.info('Output: %s', line.strip())

# Will return immediately as stdin was closed above
process.wait()
```

--------------------------------

### Expose relation endpoints

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Offers the Prometheus, Loki, and Grafana endpoints for cross-model integration.

```text
juju offer prometheus:metrics-endpoint
juju offer loki:logging
juju offer grafana:grafana-dashboard
```

--------------------------------

### Migrate Idle Agent Waiting

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Use jubilant.all_agents_idle to wait for unit agents to reach an idle state.

```python
# pytest-operator
async def test_idle(model: Model):
    await model.deploy('mycharm')
    await model.wait_for_idle()


# jubilant
def test_active(juju: jubilant.Juju):
    juju.deploy('mycharm')
    juju.wait(jubilant.all_agents_idle)
```

--------------------------------

### ops.pebble.ExecProcess.wait

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Waits for the process to finish execution.

```APIDOC
### wait()

Waits for the process to finish. If a timeout was specified during the initial exec call, this method will wait at most that duration.

#### Raises
- **ChangeError** - If there was an error starting or running the process.
- **ExecError** - If the process exits with a non-zero exit code.
```

--------------------------------

### Access the charm instance in a test

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Use the testing.Context instance as a context manager to access the charm instance, triggering an event the charm does not observe.

```python
# Charm code


class Charm(CharmBase):
    def workload_is_ready(self):
        ...  # Some business logic.
        return True


# Testing code


def test_charm_reports_workload_ready():
    ctx = testing.Context(Charm)
    state_in = testing.State(...)  # Some state to represent a ready workload.
    with ctx(ctx.on.update_status(), state_in) as mgr:
        assert mgr.charm.workload_is_ready()
        ...
```

--------------------------------

### Copy a directory tree from the container

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use pull_path to copy files recursively from the workload container to a destination directory.

```python
# copy "/source/dir/[files]" into "/destination/dir/[files]"
self.container.pull_path('/source/dir', '/destination')

# copy "/source/dir/[files]" into "/destination/[files]"
self.container.pull_path('/source/dir/*', '/destination')
```

--------------------------------

### Declare open ports in a charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-opened-ports.md

Use ops.Unit.set_ports within a charm event handler to specify which TCP ports should be open.

```python
def _on_holistic_handler(self, _: ops.EventBase):
    port = cast(int, self.config['server-port'])
    self.unit.set_ports(port)
```

--------------------------------

### Step through code with juju debug-code

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Execute hooks automatically and drop into a debugging session when breakpoints are reached.

```shell
juju debug-code myapp/0                 # debug all hooks
juju debug-code myapp/0 config-changed  # debug a specific hook
```

--------------------------------

### Client.get_checks(level, names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Retrieves the status of configured checks, optionally filtered by level or name.

```APIDOC
## Client.get_checks(level, names)

### Description
Queries the status of configured checks.

### Parameters
- **level** (CheckLevel) - Optional - The check level to query.
- **names** (Iterable[str]) - Optional - A list of check names to query.

### Returns
- **list[CheckInfo]** - A list of check status objects.
```

--------------------------------

### stop(*service_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Stop given service(s) by name.

```APIDOC
## stop(*service_names: str)

### Description
Stop given service(s) by name.
```

--------------------------------

### Observe collect-unit-status event

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Register the collect-unit-status event observer within the charm's __init__ method.

```python
# Report the unit status after each event.
framework.observe(self.on.collect_unit_status, self._on_collect_status)
```

--------------------------------

### Use Context as a context manager

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

The Context object now acts as a context manager directly, replacing deprecated run arguments and manager methods.

```python
# Older Scenario code.
ctx = Context(MyCharm)
state = ctx.run("start", pre_event=lambda charm: charm.prepare(), state=State())

ctx = Context(MyCharm)
with ctx.manager("start", State()) as mgr:
    mgr.charm.prepare()
assert mgr.output....

# Scenario 7.x
ctx = Context(MyCharm)
with ctx(ctx.on.start(), State()) as mgr:
    mgr.charm.prepare()
    out = mgr.run()
    assert out...
```

--------------------------------

### Configure secret rotation policy

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use the rotate parameter in add_secret to define a rotation schedule and observe the secret_rotate event.

```python
class MyDatabaseCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(self.on.secret_rotate, self._on_secret_rotate)

    ...  # as before

    def _on_database_relation_joined(self, event: ops.RelationJoinedEvent):
        content = {
            'username': 'admin',
            'password': 'admin',
        }
        secret = self.app.add_secret(
            content, label='secret-for-webserver-app', rotate=SecretRotate.DAILY
        )

    def _on_secret_rotate(self, event: ops.SecretRotateEvent):
        # this will be called once per day.
        if event.secret.label == 'secret-for-webserver-app':
            self._rotate_webserver_secret(event.secret)
```

--------------------------------

### Execute a command and wait for exit

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Executes a command without capturing output and waits for the process to complete.

```python
>>> process = client.exec(['send-emails'])
>>> process.wait()
```

--------------------------------

### Documenting Juju Version Dependencies

Source: https://github.com/canonical/operator/blob/main/AGENTS.md

Use the jujuadded directive within docstrings to specify Juju version requirements.

```python
def new_feature():
    """Do something new.

    .. jujuadded:: 3.5
        Further functionality was added in Juju 3.6.
    """
```

--------------------------------

### Define named breakpoints in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Use ops.Framework.breakpoint to define specific points in your charm code to pause execution.

```python
class MyCharm(ops.CharmBase):
    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        # 'config-start' is an arbitrary string you use with `--at`
        self.framework.breakpoint('config-start')
        new_val = self.config['setting']
        # ... process the new value ...
        self.framework.breakpoint('config-end')
```

--------------------------------

### Construct Prometheus URL

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

The URL format used to access the Prometheus metrics explorer.

```text
http://10.112.13.157:31471/cos-lite-prometheus-0/graph
```

--------------------------------

### Import modules instead of objects

Source: https://github.com/canonical/operator/blob/main/STYLE.md

Prefer importing modules over specific objects to maintain clear namespaces, with an exception for the typing module.

```python
from ops import CharmBase, PebbleReadyEvent
from subprocess import run


class MyCharm(CharmBase):
    def _pebble_ready(self, event: PebbleReadyEvent):
        run(['echo', 'foo'])
```

```python
import ops
import subprocess


class MyCharm(ops.CharmBase):
    def _pebble_ready(self, event: ops.PebbleReadyEvent):
        subprocess.run(['echo', 'foo'])


# However, "from typing import Foo" is okay to avoid verbosity
from typing import Optional, Tuple

counts: Optional[Tuple[str, int]]
```

--------------------------------

### Unit Testing Charm Actions

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Verify action execution, logs, and results using the Context object. Use pytest.raises to handle ActionFailed exceptions when an action fails.

```python
from ops import testing


def test_backup_action():
    ctx = testing.Context(MyCharm)
    ctx.run(
        ctx.on.action('snapshot', params={'filename': 'db-snapshot.tar.gz'}),
        testing.State(),
    )
    assert ctx.action_logs == [
        'Starting snapshot',
        'Table1 complete',
        'Table2 complete',
    ]
    assert 'snapshot-size' in ctx.action_results
```

```python
def test_backup_action_failed():
    ctx = testing.Context(MyCharm)

    with pytest.raises(testing.ActionFailed) as exc_info:
        ctx.run(ctx.on.action('do-backup'), State())
    assert exc_info.value.message == "sorry, couldn't do the backup"
    # The state is also available if that's required:
    assert exc_info.value.state.get_container(...)

    # You can still assert action results and logs that occurred as well as the failure:
    assert ctx.action_logs == ['baz', 'qux']
    assert ctx.action_results == {'foo': 'bar'}
```

--------------------------------

### Observe and handle secrets with labels

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use labels in the observer charm to identify which secret has changed during relation or secret-changed events.

```python
class MyWebserverCharm(ops.CharmBase):
    ...  # as before

    def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
        secret_id = event.relation.data[event.app]['secret-id']
        secret = self.model.get_secret(id=secret_id, label='database-secret')
        content = secret.get_content()
        self._configure_db_credentials(content['username'], content['password'])

    def _on_secret_changed(self, event: ops.SecretChangedEvent):
        if event.secret.label == 'database-secret':
            content = event.secret.get_content(refresh=True)
            self._configure_db_credentials(
                content['username'], content['password']
            )
        elif event.secret.label == 'my-other-secret':
            self._handle_other_secret_changed(event.secret)
        else:
            pass  # ignore other labels (or log a warning)
```

--------------------------------

### View service logs via kubectl

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Access service logs written to stdout by the Pebble server using standard Kubernetes log commands.

```default
microk8s kubectl logs -n snappass snappass-test-0 -c redis
```

--------------------------------

### Create a Juju user secret

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Creates a Juju user secret to store the username and password for Pebble metrics authentication.

```bash
juju add-secret metrics-user-password username=test password=test
```

--------------------------------

### Test invalid configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Add a test case to ensure the charm enters a blocked status when provided with an invalid configuration value.

```python
def test_block_on_invalid_config(charm: pathlib.Path, juju: jubilant.Juju):
    """Check that the charm goes into blocked status if slug is invalid."""
    juju.config("tinyproxy", {"slug": "foo/bar"})
    juju.wait(jubilant.all_blocked)
    juju.config("tinyproxy", reset="slug")
```

--------------------------------

### Handle storage-detaching event in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-storage.md

Define the event handler to perform cleanup or status updates when storage is being released.

```python
def _on_storage_detaching(self, event: ops.StorageDetachingEvent):
    """Handle the storage being detached."""
    self.unit.status = ops.ActiveStatus(
        'Caching disabled; provide storage to boost performance'
    )
```

--------------------------------

### Run actions

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Uses juju.run to trigger charm actions, returning a task object with built-in error checking.

```python
# pytest-operator
app = model.applications['postgresl-k8s']
action = await app.units[0].run_action('get-password', username='operator')
await action.wait()
password = action.results['password']

# jubilant
task = juju.run('postgresql-k8s/0', 'get-password', {'username': 'operator'})
password = task.results['password']
```

--------------------------------

### Define the charm class in src/charm.py

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

The charm class inherits from ops.CharmBase and serves as the entry point for Juju events.

```python
#!/usr/bin/env python3

"""Kubernetes charm for a demo app."""

import ops

import fastapi_demo


class FastAPIDemoCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)


if __name__ == "__main__":  # pragma: nocover
    ops.main(FastAPIDemoCharm)
```

--------------------------------

### Simulate API traffic

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

A shell script to generate continuous traffic and trigger error responses for monitoring.

```sh
#!/bin/sh

unit_location="10.1.157.94:8000"  # Get the IP address from 'juju status'

while true; do
    for i in {1..3}; do
        curl "http://$unit_location/names"
        echo
        sleep 5
    done

    curl "http://$unit_location/error"
    echo
    sleep 5
done
```

--------------------------------

### Inject Local Operator Code into Charm

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Script to replace the ops folder in a packed .charm file with a local version.

```bash
#!/usr/bin/env bash

if [ "$#" -lt 2 ]
then
	echo "Inject local copy of Python Operator Framework source into charm"
	echo
    echo "usage: inject-ops.sh file.charm /path/to/ops/dir" >&2
    exit 1
fi

if [ ! -f "$2/framework.py" ]; then
    echo "$2/framework.py not found; arg 2 should be path to 'ops' directory"
    exit 1
fi

set -ex

mkdir inject-ops-tmp
unzip -q $1 -d inject-ops-tmp
rm -rf inject-ops-tmp/venv/ops
cp -r $2 inject-ops-tmp/venv/ops
cd inject-ops-tmp
zip -q -r ../inject-ops-new.charm .
cd ..
rm -rf inject-ops-tmp
rm $1
mv inject-ops-new.charm $1
```

--------------------------------

### Observe relation-created event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Register an event handler for the relation-created event within the charm's __init__ method.

```python
framework.observe(self.on.db_relation_created, self._on_db_relation_created)
```

--------------------------------

### Test charm status based on leadership

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Uses pytest parametrization to verify charm behavior under different leadership states.

```python
import pytest


class MyCharm(ops.CharmBase):
    def __init__(self, framework):
        super().__init__(framework)
        framework.observe(self.on.start, self._on_start)

    def _on_start(self, _):
        if self.unit.is_leader():
            self.unit.status = ops.ActiveStatus('I rule')
        else:
            self.unit.status = ops.ActiveStatus('I am ruled')


@pytest.mark.parametrize('leader', (True, False))
def test_status_leader(leader):
    ctx = testing.Context(MyCharm, meta={'name': 'foo'})
    state_out = ctx.run(ctx.on.start(), testing.State(leader=leader))
    assert state_out.unit_status == ops.ActiveStatus(
        'I rule' if leader else 'I am ruled'
    )
```

--------------------------------

### Set the workload version

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Retrieve the workload version and expose it to Juju using the unit object.

```python
# Set the workload version of this charm.
version = fastapi_demo.get_version(port=8000)
self.unit.set_workload_version(version)
```

--------------------------------

### Write Negative Path Test

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Verifies that no data is published when the remote end has not provided required information.

```python
from interface_tester import Tester
from scenario import State, Relation


def test_nothing_happens_if_remote_empty():
    # GIVEN that the remote end has not published any tables
    t = Tester(
        State(
            leader=True,
            relations={
                Relation(
                    endpoint='my-fancy-database',  # the name doesn't matter
                    interface='my_fancy_database',
                )
            },
        )
    )
    # WHEN the database charm receives a relation-joined event
    state_out = t.run('my-fancy-database-relation-joined')
    # THEN no data is published to the (local) databags
    t.assert_relation_data_empty()
```

--------------------------------

### Define interface schema

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Define the Pydantic models for provider and requirer data bags in schema.py.

```python
# schema.py

from interface_tester.schema_base import DataBagSchema
from pydantic import BaseModel, AnyHttpUrl, Field, Json
import typing


class ProviderUnitData(BaseModel):
    secret_id: str = Field(
        description='Secret ID for the key you need in order to query this unit.',
        title='Query key secret ID',
        examples=['secret:12312323112313123213'],
    )


class ProviderAppData(BaseModel):
    api_endpoint: AnyHttpUrl = Field(
        description="URL to the database's endpoint.",
        title='Endpoint API address',
        examples=['https://example.com/v1/query'],
    )


class ProviderSchema(DataBagSchema):
    app: ProviderAppData
    unit: ProviderUnitData


class RequirerAppData(BaseModel):
    tables: Json[typing.List[str]] = Field(
        description='Tables that the requirer application needs.',
        title='Requested tables.',
        examples=[['users', 'passwords']],
    )


class RequirerSchema(DataBagSchema):
    app: RequirerAppData
    # we can omit `unit` because the requirer makes no use of the unit databags
```

--------------------------------

### Modify charm configuration

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Commands to update and reset charm configuration options.

```text
juju config tinyproxy slug=foo
```

```text
curl <address>:8000/foo/
```

```text
curl <address>:8000/example/
```

```default
juju config tinyproxy slug=foo/bar
```

```default
juju config tinyproxy --reset slug
```

--------------------------------

### Forward debugpy port from Multipass VM

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Use SSH port forwarding to connect a host-based VS Code debugger to a charm unit running inside a Multipass VM.

```shell
# 1. Get the unit IP from inside the VM:
UNIT_IP=$(multipass exec <vm-name> -- juju show-unit myapp/0 --format json \
  | jq -r '.["myapp/0"]["public-address"]')

# 2. Get the VM's IP:
VM_IP=$(multipass info <vm-name> --format json | jq -r '.info["<vm-name>"].ipv4[0]')

# 3. If necessary, make sure that you are authorised to SSH into the VM, for example by adding your SSH public key to `~/.ssh/authorized_keys` on the VM.

# 4. Forward the debugpy port through the VM to your host:
ssh -N -L 5678:${UNIT_IP}:5678 ubuntu@${VM_IP}
```

--------------------------------

### Add pathops dependency

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Include the pathops library in your project's dependencies.

```toml
dependencies = [
    "charmlibs-pathops>=1,<2",
    # ...
]
```

--------------------------------

### List recent Pebble operations

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

View the change log to identify failed operations.

```text
$ pebble changes
ID  Status  Spawn               Ready               Summary
1   Done    today at 02:05 UTC  today at 02:05 UTC  Autostart service "myapp"
2   Error   today at 02:09 UTC  today at 02:09 UTC  Start service "myapp"
```

--------------------------------

### Fetch check status in Python

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Use the container object to retrieve a specific check and verify its status against the Pebble CheckStatus enum.

```python
container = self.unit.get_container('main')
check = container.get_check('uptime')
if check.status != ops.pebble.CheckStatus.UP:
    logger.error('Uh oh, uptime check unhealthy: %s', check)
```

--------------------------------

### Define config_changed handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Implement the handler to trigger a workload replan when configuration changes.

```python
def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
    self._replan_workload()
```

--------------------------------

### get_relation_data(relation_id: int, app_or_unit: str | Application | Unit) -> Mapping[str, str]

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Retrieves the relation data bucket for a specific application or unit in a given relation.

```APIDOC
## get_relation_data(relation_id: int, app_or_unit: str | Application | Unit) -> Mapping[str, str]

### Description
Get the relation data bucket for a single app or unit in a given relation. This ignores safety checks regarding data visibility.

### Parameters
- **relation_id** (int) - Required - The relation whose content we want to look at.
- **app_or_unit** (str | Application | Unit) - Required - An Application or Unit instance, or its name, whose data we want to read.

### Returns
- **Mapping[str, str]** - A dict containing the relation data for app_or_unit or None.

### Errors
- **KeyError** - Raised if relation_id doesn't exist.
```

--------------------------------

### Unit test a failing Pebble check

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Use the CheckInfo class to simulate a failed check event during charm unit testing.

```python
import ops
from ops import testing

def test_http_check_failing():
    ctx = testing.Context(PostgresCharm)
    check_info = testing.CheckInfo(
        'http-test',
        failures=3,
        status=ops.pebble.CheckStatus.DOWN,
        level=layer.checks['http-test'].level,
        startup=layer.checks['http-test'].startup,
        threshold=layer.checks['http-test'].threshold,
    )
    layer = ops.pebble.Layer({
        'checks': {'http-test': {'override': 'replace', 'startup': 'enabled', 'failures': 3}},
    })
    container = testing.Container('db', check_infos={check_info}, layers={'layer1': layer})
    state_in = testing.State(containers={container})

    state_out = ctx.run(ctx.on.pebble_check_failed(container, info=check_info), state_in)

    assert state_out...
```

--------------------------------

### get_checks(*check_names: str, level: CheckLevel | None = None) -> CheckInfoMapping

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Fetch and return a mapping of check information indexed by check name.

```APIDOC
## get_checks

### Description
Fetch and return a mapping of check information indexed by check name.

### Parameters
- **check_names** (str) - Optional - Optional check names to query for.
- **level** (CheckLevel) - Optional - Optional check level to query for.
```

--------------------------------

### Test charm lifecycle events

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Verifies the charm's behavior during stop and remove lifecycle events.

```python
def test_stop(tinyproxy_configured: MockTinyproxy):
    """Test that the charm correctly handles the stop event."""
    ctx = testing.Context(TinyproxyCharm)
    state_out = ctx.run(ctx.on.stop(), testing.State())
    assert state_out.unit_status == testing.MaintenanceStatus("Waiting for tinyproxy to start")
    assert not tinyproxy_configured.is_running()
```

```python
def test_remove(tinyproxy_installed: MockTinyproxy):
    """Test that the charm correctly handles the remove event."""
    ctx = testing.Context(TinyproxyCharm)
    state_out = ctx.run(ctx.on.remove(), testing.State())
    assert state_out.unit_status == testing.MaintenanceStatus(
        "Waiting for tinyproxy to be installed"
    )
    assert not tinyproxy_installed.is_installed()
```

--------------------------------

### notify

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Record an occurrence of a notice with the specified options.

```APIDOC
## notify(type, key, data=None, repeat_after=None)

### Description
Record an occurrence of a notice with the specified options.

### Parameters
- **type** (NoticeType) - Required - Notice type.
- **key** (str) - Required - Notice key (format: example.com/path).
- **data** (dict[str, str] | None) - Optional - Data fields for this notice.
- **repeat_after** (timedelta | None) - Optional - Only allow this notice to repeat after this duration has elapsed.

### Returns
- **str** - The notice’s ID.
```

--------------------------------

### pull_path(source_path: str | PurePath | Iterable[str | PurePath], dest_dir: str | Path)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Recursively pulls a remote path or files to the local system.

```APIDOC
## pull_path(source_path: str | PurePath | Iterable[str | PurePath], dest_dir: str | Path)

### Description
Recursively pull a remote path or files to the local system. Only regular files and directories are copied.

### Parameters
- **source_path** (str | PurePath | Iterable[str | PurePath]) - Required - A single path or list of paths to pull from the remote system.
- **dest_dir** (str | Path) - Required - Local destination directory inside which the source dir/files will be placed.
```

--------------------------------

### Retrieve virtual machine network information

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Identify the host machine's IP address using the multipass utility.

```text
multipass info juju-sandbox-k8s
```

--------------------------------

### Verify charm version in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-charm-version.md

Check the charm version in an integration test by inspecting the Juju status output.

```python
def test_charm_version_is_set(juju: jubilant.Juju):
    """Verify that the charm version has been set."""
    version = juju.status().apps['your-app'].charm_version
    expected_version = subprocess.check_output([
        'git',
        'rev-parse',
        'HEAD',
    ]).decode('utf8')
    assert version == expected_version
```

--------------------------------

### Monitor deployment status

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/create-a-minimal-kubernetes-charm.md

Watches the Juju deployment status to confirm the application is active.

```text
juju status --watch 1s
```

```text
Model    Controller     Cloud/Region  Version  SLA          Timestamp
testing  concierge-k8s  k8s           3.6.13   unsupported  13:38:19+01:00

App           Version  Status  Scale  Charm         Channel  Rev  Address         Exposed  Message
fastapi-demo  2.1.0    active      1  fastapi-demo             0  10.152.183.215  no

Unit             Workload  Agent  Address      Ports  Message
fastapi-demo/0*  active    idle   10.1.157.73
```

--------------------------------

### Construct Grafana URL

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

The resulting URL format used to access the Grafana web interface from the host machine.

```text
http://10.112.13.157:31471/cos-lite-grafana
```

--------------------------------

### Monitor charm events

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Watch Juju logs and display charm events in a formatted table.

```shell
jhack tail myapp
```

--------------------------------

### Python Import Style

Source: https://github.com/canonical/operator/blob/main/AGENTS.md

Import modules rather than individual objects, with the exception of the typing module.

```python
# DO: Import modules, not objects (except typing)
import ops
import subprocess
from typing import Generator  # typing is an exception


class MyCharm(ops.CharmBase):
    def handler(self, event: ops.PebbleReadyEvent):
        subprocess.run(['echo', 'hello'])


# DON'T: Import objects directly
from ops import CharmBase, PebbleReadyEvent  # Avoid this
```

--------------------------------

### Test blocked status without database

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Ensures the charm enters a blocked status when the required database relation is missing.

```python
def test_no_database_blocked(mock_version):
    ctx = testing.Context(FastAPIDemoCharm)
    container = testing.Container(
        name="demo-server", can_connect=True, layers={"rock": ROCK_LAYER}
    )
    state_in = testing.State(
        containers={container},
        leader=True,
    )  # We've omitted relation data from the input state.

    state_out = ctx.run(ctx.on.collect_unit_status(), state_in)

    assert state_out.unit_status == testing.BlockedStatus("Waiting for database relation")
```

--------------------------------

### Integration test with Jubilant

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Verify charm behavior during integration with another application using the Juju client.

```python
import pathlib

import jubilant


# This assumes that your integration tests already include the standard
# build and deploy test.


def test_active_with_another_app(charm: pathlib.Path, juju: jubilant.Juju):
    juju.deploy('another-app')
    juju.integrate('your-app:endpoint', 'another-app:endpoint')
    juju.wait(jubilant.all_active)
```

--------------------------------

### set_leader(is_leader: bool = True)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Sets the leadership status of the unit.

```APIDOC
## set_leader(is_leader: bool = True)

### Description
Sets whether this unit is the leader or not. If the charm becomes a leader, the leader_elected event will be triggered.

### Parameters
- **is_leader** (bool) - Optional - Whether this unit is the leader. Defaults to True.
```

--------------------------------

### Test reverse proxy

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Verify the proxy functionality using curl.

```text
curl <address>:8000/example/
```

```text
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

```text
curl http://example.com
```

--------------------------------

### Define a peer relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Add a peers block to your charmcraft.yaml to enable peer relation functionality.

```yaml
peers:
  charm-peer:
    interface: my_charm_peers
```

--------------------------------

### Configure log file append mode

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Set pytest to append logs to the existing file instead of overwriting.

```toml
[tool.pytest.ini_options]
log_file_mode = "a"
...
```

--------------------------------

### Validate application connectivity

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Send an HTTP request to the application on the updated port to verify it is reachable.

```text
curl 10.1.157.74:5000/version
```

--------------------------------

### Observe Pebble check events

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Observe check failure and recovery events and switch on the check name to perform specific actions.

```python
class PostgresCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        # Note that "db" is the workload container's name
        framework.observe(
            self.on['db'].pebble_check_failed, self._on_pebble_check_failed
        )
        framework.observe(
            self.on['db'].pebble_check_recovered,
            self._on_pebble_check_recovered,
        )

    def _on_pebble_check_failed(self, event: ops.PebbleCheckFailedEvent):
        if event.info.name == 'http-test':
            logger.warning('The http-test has started failing!')
            self.unit.status = ops.ActiveStatus('Degraded functionality ...')

        elif event.info == 'online':
            logger.error('The service is no longer online!')

    def _on_pebble_check_recovered(self, event: ops.PebbleCheckRecoveredEvent):
        if event.info.name == 'http-test':
            logger.warning('The http-test has stopped failing!')
            self.unit.status = ops.ActiveStatus()

        elif event.info == 'online':
            logger.error('The service is online again!')
```

--------------------------------

### Monitor Juju status

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Check the status of the deployment and verify the active relations.

```text
juju status --relations --watch 1s
```

--------------------------------

### detach_storage(storage_id: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Simulates the detachment of a storage device.

```APIDOC
## detach_storage(storage_id: str)

### Description
Detach a storage device, simulating a `juju detach-storage` call. It will trigger a storage-detaching hook if the storage unit exists and is attached.

### Parameters
- **storage_id** (str) - Required - The full storage ID of the storage unit (e.g., my-storage/0).
```

--------------------------------

### Manage model lifecycle with pytest-jubilant

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Commands to deploy and reuse models across test runs to avoid redeployment.

```text
# First run: deploy and keep the models
tox -e integration -- --juju-model mytest --no-juju-teardown
# Subsequent runs: skip deployment, reuse the models
tox -e integration -- --juju-model mytest --no-juju-setup --no-juju-teardown
```

--------------------------------

### send_signal(sig, *service_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Send a signal to one or more services.

```APIDOC
## send_signal(sig: int | str, *service_names: str)

### Description
Send the given signal to one or more services.

### Parameters
- **sig** (int | str) - Required - Name or number of signal to send.
- **service_names** (str) - Required - Name(s) of the service(s) to send the signal to.
```

--------------------------------

### add_network(address, *, endpoint, relation_id, cidr, interface, ingress_addresses, egress_subnets)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Adds simulated network data for a given relation endpoint or binding.

```APIDOC
## add_network

### Description
Adds simulated network data for the given relation endpoint (binding). Calling this multiple times with the same (binding, relation_id) combination will replace the associated network data.

### Parameters
- **address** (str) - Required - Binding’s IPv4 or IPv6 address.
- **endpoint** (str) - Optional - Name of relation endpoint (binding) to add network data for.
- **relation_id** (int) - Optional - Relation ID for the binding.
- **cidr** (str) - Optional - Binding’s CIDR.
- **interface** (str) - Optional - Name of network interface.
- **ingress_addresses** (Iterable[str]) - Optional - List of ingress addresses.
- **egress_subnets** (Iterable[str]) - Optional - List of egress subnets.

### Raises
- **ModelError** - If the endpoint is not a known relation name, or the relation_id is incorrect.
- **ValueError** - If address is not an IPv4 or IPv6 address.
```

--------------------------------

### Manage SSH keys for Juju 4

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Commands to add or import SSH keys required for Juju 4 authentication.

```shell
juju add-ssh-key "$(cat ~/.ssh/id_ed25519.pub)"
```

```shell
juju import-ssh-key gh:<your-github-username>
```

--------------------------------

### Verify Loki logs via HTTP API

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Test function and helper to query the Loki API for application logs.

```python
def test_loki_data(charm: pathlib.Path, cos: jubilant.Juju):
    """Use Loki's HTTP API to verify that Loki has a label for our app.

    COS Lite exposes Loki's API through the Traefik load balancer. Traefik comes with an action
    that tells us the base URL of Loki's API.
    """
    task = cos.run("traefik/0", "show-proxied-endpoints")
    results = json.loads(task.results["proxied-endpoints"])
    loki_url = results["loki/0"]["url"]
    loki_api_url = f"{loki_url}/loki/api/v1/label/juju_application/values"
    juju_applications = _get_loki_logs(loki_api_url)
    assert juju_applications is not None, "No logs available from Loki"
    assert APP_NAME in juju_applications


def _get_loki_logs(loki_api_url: str) -> list[str] | None:
    """Wait for logs to be available from Loki and return them."""
    for attempt in range(3 * 60):
        if attempt:  # If not the first attempt, wait before retrying.
            time.sleep(1)
        try:
            response = urllib.request.urlopen(loki_api_url)
        except urllib.error.URLError:
            continue
        response_decoded = json.loads(response.read())
        if "data" in response_decoded:
            return response_decoded["data"]
    return None
```

--------------------------------

### Update test_deploy for blocked status

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Modify the initial deployment test to expect a blocked status when the charm is missing its required database relation.

```python
@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    """Deploy the charm under test.

    Assert on the unit status before any relations/configurations take place.
    """
    resources = {
        "demo-server-image": METADATA["resources"]["demo-server-image"]["upstream-source"]
    }

    # Deploy the charm and wait for it to report blocked, as it needs Postgres.
    juju.deploy(charm, app=APP_NAME, resources=resources)
    juju.wait(jubilant.all_blocked)
```

--------------------------------

### Configure auto-restart on check failure

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Define the on-check-failure map within a service configuration to trigger a restart, shutdown, or ignore action when a specific check fails.

```yaml
services:
    server:
        override: merge
        on-check-failure:
            http-test: restart   # can also be "shutdown" or "ignore" (the default)
```

--------------------------------

### Peek at a new secret revision

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use peek_content to inspect secret contents before deciding to update to a new revision.

```python
def _on_secret_changed(self, event: ops.SecretChangedEvent):
    content = event.secret.peek_content()
    if not self._valid_password(content.get('password')):
        logger.warning('Invalid credentials! Not updating to new revision.')
        return
    content = event.secret.get_content(refresh=True)
    ...
```

--------------------------------

### Read a file from the workload container

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-files-in-the-workload-container.md

Use read_text to retrieve the contents of a file from the workload container.

```python
backup = (self.myapp_root / 'backup.yaml').read_text()
```

--------------------------------

### Observe leader-elected event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-leadership-changes.md

Register the leader-elected event observer within the charm's __init__ method.

```python
self.framework.observe(self.on.leader_elected, self._on_leader_elected)
```

--------------------------------

### Intercept hooks with juju debug-hooks

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Use these commands to open a tmux session on a unit and intercept hook execution.

```shell
juju debug-hooks myapp/0                 # intercept all hooks and actions
juju debug-hooks myapp/0 config-changed  # intercept only config-changed
```

--------------------------------

### Define Loki relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Add the logging endpoint to the requires section of your charmcraft.yaml file to declare the loki_push_api interface.

```yaml
requires:
  database:
    interface: postgresql_client
    limit: 1
    optional: false
  logging:
    interface: loki_push_api
    optional: true
```

--------------------------------

### Publish Relation Data in Charm

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Implementation of data publication to a relation using the defined Pydantic model and ops.Relation.save.

```python
receiver_protocol_to_transport_protocol: dict[str, TransportProtocolType] = {
    'zipkin': TransportProtocolType.HTTP,
    'otlp_grpc': TransportProtocolType.GRPC,
    'otlp_http': TransportProtocolType.HTTP,
    'jaeger_thrift_http': TransportProtocolType.HTTP,
    'jaeger_grpc': TransportProtocolType.GRPC,
}


def _publish_provider(
    self, relation: ops.Relation, receivers: Iterable[tuple[str, str]]
):
    data = TracingProviderAppData(
        receivers=[
            Receiver(
                url=url,
                protocol=ProtocolType(
                    name=protocol,
                    type=receiver_protocol_to_transport_protocol[protocol],
                ),
            )
            for protocol, url in receivers
        ],
    )
    relation.save(data, self._charm.app)
```

--------------------------------

### Wrap website relation access

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-from-a-hooks-based-charm.md

Helper method to retrieve a relation object safely.

```python
def _get_website_relation(self) -> ops.Relation:
    # WARNING: would return None if called too early, e.g. during install
    return self.model.get_relation('website')
```

--------------------------------

### Inspect relation data

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Display relation databags for all units involved in a specific relation.

```shell
jhack show-relation myapp:database postgresql:database
```

--------------------------------

### Observe relation-changed events

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Register an observer for a specific relation change event within the charm's __init__ method.

```python
framework.observe(self.on.replicas_relation_changed, self._update_configuration)
```

--------------------------------

### Define Pydantic models for actions

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Create Python classes using Pydantic to mirror the action schema for type checking and validation.

```python
class CompressionKind(enum.Enum):
    GZIP = 'gzip'
    BZIP = 'bzip2'
    XZ = 'xz'


class Compression(pydantic.BaseModel):
    kind: CompressionKind = pydantic.Field(CompressionKind.BZIP)

    quality: int = pydantic.Field(
        5, description='Compression quality.', ge=0, le=9
    )


class SnapshotAction(pydantic.BaseModel):
    """Take a snapshot of the database."""

    filename: str = pydantic.Field(description='The name of the snapshot file.')

    compression: Compression = pydantic.Field(
        default_factory=Compression,
        description='The type of compression to use.',
    )
```

--------------------------------

### Specifying secret ownership and grants

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Define secret ownership as 'unit' or 'app' and specify remote grants to simulate access permissions.

```python
rel = testing.Relation('web')
state_in = testing.State(
    secrets={
        testing.Secret(
            {'key': 'private'},
            owner='unit',  # or 'app'
            # The secret owner has granted access to the "remote" app over some relation:
            remote_grants={rel.id: {'remote'}},
        )
    }
)
```

--------------------------------

### Handle relation-joined event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Implement the event handler to save unit-specific data to the relation databag.

```python
def _on_smtp_relation_joined(self, event: ops.RelationJoinedEvent):
    smtp_credentials_secret_id = self.create_smtp_user(event.unit.name)
    data = SMTPProviderUnitData(smtp_credentials=smtp_credentials_secret_id)
    relation.save(data, event.unit)
```

--------------------------------

### Define Prometheus relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Add a provides endpoint to your charmcraft.yaml to enable integration with the Prometheus charm.

```yaml
provides:
  metrics-endpoint:
    interface: prometheus_scrape
    optional: true
```

--------------------------------

### Add a relation unit to the harness

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Adds a remote unit to an existing relation, triggering a relation_joined event.

```default
rel_id = harness.add_relation('db', 'postgresql')
harness.add_relation_unit(rel_id, 'postgresql/0')
```

--------------------------------

### Define charm path fixture for integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Implement a pytest fixture to resolve the charm path from an environment variable or the local directory.

```python
# tests/integration/conftest.py
import os
import pathlib


@pytest.fixture(scope='session')
def charm():
    """Return the path of the charm under test."""
    # Assume the current working directory is the charm root.
    yield get_charm_path(env_var='CHARM_PATH', default_dir=pathlib.Path())


def get_charm_path(env_var: str, default_dir: pathlib.Path) -> pathlib.Path:
    charm = os.environ.get(env_var)
    if not charm:
        charms = list(default_dir.glob('*.charm'))
        assert charms, f'No charms were found in {default_dir}'
        assert len(charms) == 1, f'Found more than one charm {charms}'
        charm = charms[0]
    path = pathlib.Path(charm).resolve()
    assert path.is_file(), f'{path} is not a file'
    return path
```

--------------------------------

### Send signals to a process

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use send_signal to terminate or interact with a running process.

```python
process = container.exec(['sleep', '10'])
time.sleep(1)
process.send_signal(signal.SIGTERM)
process.wait()
```

--------------------------------

### ops.hookcmds.opened_ports

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

List all ports or port ranges opened by the unit.

```APIDOC
## ops.hookcmds.opened_ports(*, endpoints: bool = False)

### Description
List all ports or port ranges opened by the unit.

### Parameters
- **endpoints** (bool) - Optional - If True, each entry in the port list will be augmented with a list of endpoints.
```

--------------------------------

### Verify workload version in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-the-workload-version.md

Check the application version attribute from the Juju model status during integration testing.

```python
import pathlib

import jubilant
import pytest


@pytest.mark.juju_setup
def test_deploy(charm: pathlib.Path, juju: jubilant.Juju):
    """Deploy the charm under test."""
    juju.deploy(f'./{charm}')
    juju.wait(jubilant.all_active)


def test_workload_version_is_set(juju: jubilant.Juju):
    # Verify that the workload version has been set.
    version = juju.status().apps['your-app'].version
    # We'll need to update this version every time we upgrade to a new workload
    # version. If the workload has an API or some other way of getting the
    # version, the test should get it from there and use that to compare to the
    # unit setting.
    assert version == '3.14'
```

--------------------------------

### Check Pebble connectivity

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Verify if the Pebble API is reachable before performing operations to avoid connection errors.

```python
# Add status based on any earlier errors communicating with Pebble.
...
# Check that Pebble is still reachable now.
container = self.unit.get_container("example")
if not container.can_connect():
    event.add_status(ops.MaintenanceStatus("Waiting for Pebble..."))
```

--------------------------------

### Testing secret removal events

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Verify that the charm correctly handles secret-remove events by checking the context's removed_secret_revisions.

```python
class SecretCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.secret_remove, self._on_secret_remove)

    def _on_secret_remove(self, event: ops.SecretRemoveEvent):
        event.remove_revision()


ctx = testing.Context(SecretCharm)
secret = testing.Secret({'password': 'xxxxxxxx'}, owner='app')
old_revision = 42
state_out = ctx.run(
    ctx.on.secret_remove(secret, revision=old_revision),
    testing.State(leader=True, secrets={secret}),
)
assert ctx.removed_secret_revisions == [old_revision]
```

--------------------------------

### SSH into the workload container

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Access the workload container to run Pebble commands directly.

```shell
juju ssh --container myapp myapp/0
```

--------------------------------

### Inspect specific Pebble tasks

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Drill into a specific change ID to view failure details and captured logs.

```text
$ pebble tasks 2
Status  Spawn               Ready               Summary
Error   today at 02:09 UTC  today at 02:09 UTC  Start service "myapp"

......................................................................
Start service "myapp"

2026-05-22T02:09:01Z INFO Most recent service output:
    Traceback (most recent call last):
      ...
    KeyError: 'DATABASE_URL'
2026-05-22T02:09:01Z ERROR service start attempt: exited quickly with code 1, will restart
```

--------------------------------

### wait_change

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Waits for a specific change operation to complete.

```APIDOC
## wait_change(change_id: ChangeID, timeout: float | None = 30.0, delay: float = 0.1) -> Change

### Description
Waits for the given change to be ready, either by using the server's wait endpoint or by polling.

### Parameters
- **change_id** (ChangeID) - Required - The ID of the change to wait for.
- **timeout** (float | None) - Optional - Maximum time to wait.
- **delay** (float) - Optional - Polling interval if the server does not support wait endpoints.

### Returns
- **Change** - The completed Change object.
```

--------------------------------

### Observe relation-departed event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Register an observer for the relation-departed event within the charm's __init__ method.

```python
framework.observe(
    self.on.smtp_relation_departed, self._on_smtp_relation_departed
)
```

--------------------------------

### Reference Git Branch in Requirements

Source: https://github.com/canonical/operator/blob/main/HACKING.md

Use a specific Git branch for the operator dependency in requirements files.

```text
#ops ~= 3.0
git+https://github.com/{your-username}/operator@{your-branch-name}
```

--------------------------------

### Update tox.ini dependencies for Jubilant migration

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Replace juju, pytest-operator, and pytest-asyncio with jubilant and pytest-jubilant in the integration test environment.

```diff
[testenv:integration]
 deps =
     boto3
     cosl
-    juju>=3.0
+    jubilant>=1.8,<2
+    pytest-jubilant>=2,<3
     pytest
-    pytest-operator
-    pytest-asyncio
     -r{toxinidir}/requirements.txt
```

--------------------------------

### Guard operations with leadership check

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-leadership-changes.md

Use is_leader() to restrict sensitive operations to the leader unit, noting that leadership status should be re-verified for long-running tasks.

```python
if self.unit.is_leader():
    secret = self.model.get_secret(label='my-label')
    secret.set_content({'username': 'user', 'password': 'pass'})
```

--------------------------------

### Client.get_change(change_id)

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Retrieves details for a single change by its unique identifier.

```APIDOC
## Client.get_change(change_id)

### Description
Fetches a single change object by its ID.

### Parameters
- **change_id** (ChangeID) - Required - The ID of the change to retrieve.

### Returns
- **Change** - The change object.
```

--------------------------------

### Report application status via collect_app_status

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Observe the collect_app_status event to report application-wide status, which is triggered only for the leader unit.

```python
class DemoServerCharm(ops.CharmBase):
    """Manage the server."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(
            self.on.collect_app_status, self._on_collect_app_status
        )
        framework.observe(
            self.on.collect_unit_status, self._on_collect_unit_status
        )
        # Observe other events...

    def _on_collect_app_status(self, event: ops.CollectStatusEvent):
        # This is triggered for the leader unit only.
        num_degraded = ...  # Inspect peer unit databags to find degraded units.
        if num_degraded:
            event.add_status(
                ops.ActiveStatus(f'degraded units: {num_degraded}')
            )
            return
        event.add_status(ops.ActiveStatus())

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent):
        # This is triggered for each unit.
        if (
            self.is_degraded()
        ):  # Use a custom helper method to determine status.
            event.add_status(ops.ActiveStatus('degraded'))
            return
        event.add_status(ops.ActiveStatus())
```

--------------------------------

### Fixed state-transition test with container

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

The corrected test definition that includes a mock container in the input state.

```python
def test_get_value_action():
    ctx = testing.Context(DemoCharm)
    container = testing.Container('my-container', can_connect=True)
    state_in = testing.State(containers={container})
    ctx.run(ctx.on.action('get-value', params={'value': 'foo'}), state_in)
    assert ctx.action_results == {'out-value': 'foo'}
```

--------------------------------

### Test relation changes with Context

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Uses Context.on.relation_changed to verify that the charm correctly updates workload configuration based on new relation data.

```python
import pytest
from ops import testing

from charm import DemoCharm


def test_relation_changed(monkeypatch: pytest.MonkeyPatch):
    ctx = testing.Context(DemoCharm)
    workload = MockWorkload('foo.local:1234')
    monkeypatch.setattr(
        'charm.DemoCharm.write_workload_config', workload.write_config
    )
    relation = testing.Relation(
        endpoint='database',
        remote_app_data={'endpoints': 'bar.local:5678'},
    )
    state_in = testing.State(relations={relation})
    ctx.run(ctx.on.relation_changed(relation), state_in)
    assert workload.config == 'bar.local:5678'
```

--------------------------------

### Update Pebble ready handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Update the PebbleReadyEvent handler to utilize the shared _replan_workload method.

```python
def _on_demo_server_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
    self._replan_workload()
```

--------------------------------

### Import Pydantic in charm.py

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Adds the necessary import statement to the top of the charm file.

```python
import pydantic
```

--------------------------------

### Define leader-elected event handler

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-leadership-changes.md

Implement the handler to perform actions such as reconfiguring the charm when the unit becomes the leader.

```python
def _on_leader_elected(self, event: ops.LeaderElectedEvent):
    self.reconfigure(leader=self.unit)
```

--------------------------------

### Define Grafana relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Add the grafana-dashboard endpoint to the provides section of your charmcraft.yaml file.

```yaml
provides:
  metrics-endpoint:
    interface: prometheus_scrape
    optional: true
  grafana-dashboard:
    interface: grafana_dashboard
    optional: true
```

--------------------------------

### Handle relation-created event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Implement the event handler to save relation data, typically restricted to the leader unit.

```python
def _on_db_relation_created(self, event: ops.RelationCreatedEvent):
    if not self.unit.is_leader():
        return
    credentials = self.create_database(event.app.name)
    data = DatabaseProviderAppData(credentials=credentials)
    relation.save(data, event.app)
```

--------------------------------

### Retrieve Grafana admin password

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Use this command to fetch the administrative credentials for the Grafana instance within the cos-lite model.

```text
juju run grafana/0 -m cos-lite get-admin-password --wait 1m
```

--------------------------------

### Check service status

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Display the current status of services managed by Pebble.

```text
$ /charm/bin/pebble services
Service   Startup  Current  Since
workload  enabled  active   today at 02:05 UTC
```

--------------------------------

### Enforce keyword arguments for State components

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Use keyword arguments for State and its components instead of positional arguments.

```python
# Older Scenario code.
container1 = Container('foo', True)
state = State({'key': 'value'}, [relation1, relation2], [network], [container1, container2])

# Scenario 7.x
container1 = Container('foo', can_connect=True)
state = State(
    config={'key': 'value'},
    relations={relation1, relation2},
    networks={network},
    containers={container1, container2},
)
```

--------------------------------

### Configure pytest to treat warnings as errors

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Add filterwarnings to pyproject.toml to ensure tests fail on warnings, with options to ignore specific known warnings.

```toml
[tool.pytest.ini_options]
filterwarnings = [
    "error",
]
```

```toml
[tool.pytest.ini_options]
filterwarnings = [
    "error",
    "ignore:websockets.legacy is deprecated:DeprecationWarning",
]
```

--------------------------------

### add_relation(relation_name, remote_app, *, app_data, unit_data)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Declares a new relation between the application and a remote application.

```APIDOC
## add_relation

### Description
Declare that there is a new relation between this application and remote_app. This function creates a relation with an application and triggers a RelationCreatedEvent.

### Parameters
- **relation_name** (str) - Required - The relation on the charm that is being integrated with.
- **remote_app** (str) - Required - The name of the application that is being integrated with.
- **app_data** (Mapping[str, str]) - Optional - If provided, adds a new unit and sets application relation data.
- **unit_data** (Mapping[str, str]) - Optional - If provided, adds a new unit and sets unit relation data.

### Returns
- **int** - The ID of the relation created.
```

--------------------------------

### set_cloud_spec(spec: CloudSpec)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Sets the cloud specification metadata, including credentials, for the charm environment.

```APIDOC
## set_cloud_spec(spec: CloudSpec)

### Description
Sets the cloud specification (metadata) including credentials. This method should be called before the charm invokes ops.Model.get_cloud_spec().

### Parameters
- **spec** (CloudSpec) - Required - The cloud specification object containing metadata and credentials.
```

--------------------------------

### hooks_disabled()

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

A context manager to run code with hooks disabled.

```APIDOC
## hooks_disabled

### Description
A context manager to run code with hooks disabled. Events will not fire while inside this context.
```

--------------------------------

### ops.hookcmds.relation_list

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Lists units participating in a relation.

```APIDOC
## ops.hookcmds.relation_list(id: int | None = None, *, endpoint: str | None = None, app: bool = False)

### Description
List relation units. Note that `id` can only be `None` if the current hook is a relation event.

### Parameters
- **id** (int | None) - Optional - The ID of the relation to list units for, or None to get data for the relation that triggered the current hook.
- **endpoint** (str | None) - Optional - If provided together with `id`, the relation is identified to Juju as `endpoint:id`.
- **app** (bool) - Optional - List remote application instead of participating units.

### Response
- **Returns** (str | list[str]) - A list of units or the remote application name.
```

--------------------------------

### get_workload_version() -> str

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Reads the workload version that was set by the unit.

```APIDOC
## get_workload_version() -> str

### Description
Read the workload version that was set by the unit.

### Returns
- **str** - The workload version.
```

--------------------------------

### Check health checks

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Verify the status of configured Pebble health checks.

```shell
/charm/bin/pebble checks
```

--------------------------------

### ops.hookcmds.relation_model_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves details about the model hosting a related application.

```APIDOC
## ops.hookcmds.relation_model_get(id: int | None = None, *, endpoint: str | None = None)

### Description
Get details about the model hosting a related application.

### Parameters
- **id** (int | None) - Optional - The ID of the relation to get data for, or None to get data for the relation that triggered the current hook.
- **endpoint** (str | None) - Optional - If provided together with `id`, the relation is identified to Juju as `endpoint:id`.

### Response
- **Returns** (RelationModel) - Details about the hosting model.
```

--------------------------------

### Configure secret expiration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Set an expiration date using the expire parameter in add_secret and handle the secret_expired event.

```python
class MyDatabaseCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(self.on.secret_expired, self._on_secret_expired)

    ...  # as before

    def _on_database_relation_joined(self, event: ops.RelationJoinedEvent):
        content = {
            'username': 'admin',
            'password': 'admin',
        }
        secret = self.app.add_secret(
            content,
            label='secret-for-webserver-app',
            expire=datetime.timedelta(days=42),
        )  # this can also be an absolute datetime

    def _on_secret_expired(self, event: ops.SecretExpiredEvent):
        # this will be called only once, 42 days after the relation-joined event.
        if event.secret.label == 'secret-for-webserver-app':
            self._rotate_webserver_secret(event.secret)
```

--------------------------------

### ops.pebble.ExecProcess.send_signal

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Sends a specified signal to the running process.

```APIDOC
### send_signal(sig: int | str)

Sends a signal to the running process. The signal can be specified by name (e.g., "SIGHUP") or by number (e.g., 1).

#### Parameters
- **sig** (int | str) - Required - The name or number of the signal to send.
```

--------------------------------

### Retrieve database relation data

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Extracts and parses database connection details from the charm's relation data.

```python
def fetch_database_relation_data(self) -> dict[str, str]:
    """Retrieve relation data from a database."""
    relations = self.database.fetch_relation_data()
    logger.debug("Got following database data: %s", relations)
    for data in relations.values():
        if not data:
            continue
        logger.info("New database endpoint is %s", data["endpoints"])
        host, port = data["endpoints"].split(":")
        db_data = {
            "db_host": host,
            "db_port": port,
            "db_username": data["username"],
            "db_password": data["password"],
        }
        return db_data
    return {}
```

--------------------------------

### ops.hookcmds.juju_log

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Write a message to the juju log.

```APIDOC
## ops.hookcmds.juju_log(message: str, *, level: Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO')

### Description
Write a message to the juju log.

### Parameters
- **message** (str) - Required - The message to log.
- **level** (str) - Optional - Send the message at the given level.
```

--------------------------------

### Update integration test timeout

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/write-your-first-machine-charm.md

Adjust the wait timeout for the charm deployment in the integration test suite.

```python
    juju.wait(jubilant.all_active, timeout=600)
```

--------------------------------

### Trigger custom events via Juju events

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Trigger custom events by executing the underlying Juju event instead of running custom events directly.

```python
# Older Scenario code.
ctx.run('my_charm_lib.on.database_created', state)

# Scenario 7.x
ctx.run(ctx.on.relation_created(relation=relation), state)
```

--------------------------------

### Observe relation-broken event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Register an observer for the relation-broken event within the charm's __init__ method.

```python
framework.observe(self.on.db_relation_broken, self._on_db_relation_broken)
```

--------------------------------

### Track a new secret revision

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Subscribe to secret-changed events and use get_content with refresh=True to track the latest secret revision.

```python
class MyWebserverCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(self.on.secret_changed, self._on_secret_changed)

    ...  # as before

    def _on_secret_changed(self, event: ops.SecretChangedEvent):
        content = event.secret.get_content(refresh=True)
        self._configure_db_credentials(content['username'], content['password'])
```

--------------------------------

### ops.hookcmds.secret_info_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves metadata information for a secret.

```APIDOC
## ops.hookcmds.secret_info_get(*, id=None, label=None)

### Description
Gets metadata for a secret identified by ID or label.

### Parameters
- **id** (str) - Optional - The ID of the secret.
- **label** (str) - Optional - The label of the secret.

### Returns
- **SecretInfo** - The secret metadata.
```

--------------------------------

### Define metrics-secret-id in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-metrics.md

Add a configuration option to store the secret ID for metrics authentication.

```yaml
config:
  options:
    metrics-secret-id:
      description: Secret ID for the metrics username and password
      type: string
```

--------------------------------

### Model Databags with Pydantic

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Python classes representing the tracing interface databag structure using Pydantic models.

```python
class TransportProtocolType(enum.Enum):
    """Receiver Type."""

    HTTP = 'http'
    GRPC = 'grpc'


class ProtocolType(pydantic.BaseModel):
    """Protocol Type."""

    name: str = pydantic.Field(
        description='Receiver protocol name. What protocols are supported (and what they are called) '
        'may differ per provider.',
        examples=[
            'otlp_grpc',
            'otlp_http',
            'tempo_http',
            'jaeger_thrift_compact',
        ],
    )
    type: TransportProtocolType = pydantic.Field(
        description='The transport protocol used by this receiver.',
        examples=['http', 'grpc'],
    )


class Receiver(pydantic.BaseModel):
    """Specification of an active receiver."""

    protocol: ProtocolType = pydantic.Field(
        description='Receiver protocol name and type.'
    )
    url: str = pydantic.Field(
        description="""URL at which the receiver is reachable. If there's an ingress, it would be the external URL.
        Otherwise, it would be the service's fqdn or internal IP.
        If the protocol type is grpc, the url will not contain a scheme.""",
        examples=[
            'http://traefik_address:2331',
            'https://traefik_address:2331',
            'http://tempo_public_ip:2331',
            'https://tempo_public_ip:2331',
            'tempo_public_ip:2331',
        ],
    )


class TracingProviderAppData(pydantic.BaseModel):
    receivers: list[Receiver] = pydantic.Field(
        description='A list of enabled receivers in the form of the protocol they use and their resolvable server url.',
    )
```

--------------------------------

### Read a user secret

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Access user-provided secrets by retrieving the secret URI from configuration and observing secret-changed events.

```python
class MyCharm(ops.CharmBase):
    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.secret_changed, self._on_secret_changed)

    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        secret_uri = self.config.get('my-secret-option')
        if not secret_uri:
            return
        # Read the secret.
        secret = self.model.get_secret(
            id=secret_uri, label='user-provided-secret'
        )
        content = secret.get_content()
        # Do something with the secret content.
        self._configure_with_secret(content)

    def _on_secret_changed(self, event: ops.SecretChangedEvent):
        if event.secret.label == 'user-provided-secret':
            # Read the secret.
            content = event.secret.get_content(refresh=True)
            # Do something with the secret content.
            self._configure_with_secret(content)
```

--------------------------------

### Test custom event emission

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-libraries.md

Verifies that the library emits the expected custom event when a relation change occurs.

```python
def test_ready_event():
    ctx = testing.Context(MyTestCharm, meta=MyTestCharm.META)
    relation = testing.Relation('database')
    secret = testing.Secret({'username': 'admin', 'password': 'admin'})
    state_in = testing.State(relations={relation}, secrets={secret})
    ctx.run(ctx.on.relation_changed(relation), state_in)
    relation_changed_event, custom_event = ctx.emitted_events
    assert isinstance(relation_changed_event, ops.RelationChangedEvent)
    assert isinstance(custom_event, DatabaseReadyEvent)
    assert custom_event.credential_secret.id == secret.id
```

--------------------------------

### Access a Kubernetes charm container via SSH

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Connect to a specific container within a Kubernetes charm pod.

```shell
juju ssh --container myworkload myapp/0
```

--------------------------------

### Inspect Pebble health checks

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-a-kubernetes-charm.md

Commands to view the status and details of configured health checks.

```shell
pebble checks                 # status of all checks
pebble check myapp-ready      # full detail for one check, in YAML
pebble check myapp-ready --refresh   # run it now instead of waiting for the next interval
pebble health                 # exit code 0 if all checks healthy, 1 otherwise
```

--------------------------------

### Update expected plan in unit tests

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/make-your-charm-configurable.md

Modify the expected Pebble plan in your unit tests to account for the service override configuration.

```python
# Expected plan after Pebble ready with default config.
expected_plan = ops.pebble.Plan(ROCK_LAYER.to_dict())
expected_plan.services["fastapi"].override = "merge"
```

--------------------------------

### Disable Hook Events

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Use this context manager to perform harness operations without triggering charm events.

```python
with harness.hooks_disabled():
    # things in here don't fire events
    harness.set_leader(True)
    harness.update_config(unset=['foo', 'bar'])
# things here will again fire events
```

--------------------------------

### Remove legacy status updates

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Remove manual status updates from the workload replan logic to favor the declarative collect-status approach.

```python
self.unit.status = ops.ActiveStatus()
```

```python
self.unit.status = ops.MaintenanceStatus("Waiting for Pebble in workload container")
```

```python
self.unit.status = ops.BlockedStatus(str(e))
```

--------------------------------

### Write data to relation databag

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Use the .data attribute to write configuration values to the application databag.

```python
def _on_config_changed(self, event: ops.ConfigChangedEvent):
    if relation := self.model.get_relation('ingress'):
        relation.data[self.app]['domain'] = self.config['domain']
```

--------------------------------

### ops.hookcmds.action_fail

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Sets the action status to failed with an optional error message.

```APIDOC
## ops.hookcmds.action_fail(message: str | None = None)

### Description
Set action fail status with message.

### Parameters
- **message** (str) - Optional - The failure error message. Juju will provide a default message if one is not provided.
```

--------------------------------

### Report unit status directly during event handling

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Set self.unit.status to update the unit status immediately when handling a specific event.

```python
def _on_start(self, event: ops.StartEvent):
    """Handle start event."""
    self.unit.status = ops.MaintenanceStatus('starting server')
    demo_server.start()
    # At the end of the handler, Ops triggers collect_unit_status.
```

--------------------------------

### get_pod_spec() -> tuple[Mapping[Any, Any], Mapping[Any, Any]]

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Returns the content of the pod spec as last set by the charm.

```APIDOC
## get_pod_spec() -> tuple[Mapping[Any, Any], Mapping[Any, Any]]

### Description
Return the content of the pod spec as last set by the charm. This returns both the pod spec and any k8s_resources that were supplied.

### Returns
- **tuple** - A tuple containing the pod spec and k8s_resources mappings.
```

--------------------------------

### ops.hookcmds.is_leader

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Obtain the current leadership status for the unit.

```APIDOC
## ops.hookcmds.is_leader()

### Description
Obtain the current leadership status for the unit the charm code is executing on. The value is accurate for 30s from the time the method is successfully called.
```

--------------------------------

### ops.tracing.set_destination(url, ca)

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Sets the destination for tracing data, allowing for custom configurations beyond standard relation databags.

```APIDOC
## ops.tracing.set_destination(url, ca)

### Description
Sets the destination for tracing data. This function is intended for scenarios where the tracing destination cannot be determined via the standard charm tracing relation databag. It is safe to call unconditionally in a reconciler pattern as repeated calls with the same arguments are no-ops.

### Parameters
- **url** (string) - Required - The full endpoint URL for tracing data (e.g., 'http://localhost/v1/traces').
- **ca** (string) - Optional - A multi-line string containing the CA list (PEM bundle) for HTTPS connections.
```

--------------------------------

### ops.pebble.Client.abort_change

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Abort a specific change by its ID.

```APIDOC
## abort_change(change_id: ChangeID) -> Change

### Description
Abort change with given ID.

### Parameters
- **change_id** (ChangeID) - Required - The ID of the change to abort.
```

--------------------------------

### Send signals to services

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-the-workload-container.md

Use send_signal to transmit signals to one or more services, raising an APIError if the service is missing or stopped.

```python
container.send_signal('SIGHUP', 'nginx', 'redis')
```

--------------------------------

### remove_path(path, *, recursive=False)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Remove a file or directory on the remote system.

```APIDOC
## remove_path(path: str | PurePath, *, recursive: bool = False)

### Description
Remove a file or directory on the remote system. Behaviourally similar to `rm -rf <file|dir>`.

### Parameters
- **path** (str | PurePath) - Required - Path of the file or directory to delete.
- **recursive** (bool) - Optional - If true, and path is a directory, recursively delete it and everything under it.
```

--------------------------------

### ops.hookcmds.state_delete(key: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Deletes server-side-state key value pairs.

```APIDOC
## ops.hookcmds.state_delete(key: str)

### Description
Delete server-side-state key value pairs.

### Parameters
- **key** (str) - Required - The key of the server-side state to delete.
```

--------------------------------

### stop_services

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Stops the specified services and waits for them to be stopped.

```APIDOC
## stop_services(services: Iterable[str], timeout: float = 30.0, delay: float = 0.1) -> ChangeID

### Description
Stops the specified services and polls for their status.

### Parameters
- **services** (Iterable[str]) - Required - Non-empty list of service names to stop.
- **timeout** (float) - Optional - Seconds to wait for the stop to complete.
- **delay** (float) - Optional - Seconds to wait before executing the stop.

### Returns
- **ChangeID** - The ID of the stop change operation.
```

--------------------------------

### Execute commands

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Uses juju.exec to run shell commands on a unit, which automatically handles error checking.

```python
# pytest-operator
unit = model.applications['discourse-k8s'].units[0]
action = await unit.run('/bin/bash -c "..."')
await action.wait()
logger.info(action.results)
assert action.results['return-code'] == 0, 'Enable plugins failed'

# jubilant
task = juju.exec('/bin/bash -c "..."', unit='discourse-k8s/0')
logger.info(task.results)
```

--------------------------------

### Define unit relation data schema

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Define a Pydantic model for unit-specific relation data.

```python
class SMTPProviderUnitData(pydantic.BaseModel):
    smtp_credentials: str = pydantic.Field(description='A Juju secret ID')
```

--------------------------------

### Use relative imports inside packages

Source: https://github.com/canonical/operator/blob/main/STYLE.md

Use relative imports with a dot for internal package references to avoid absolute path dependencies.

```python
from ops import charm
```

```python
from . import charm

# Or, if you need to avoid adding the public name "charm" to the namespace:

from . import charm as _charm
```

--------------------------------

### Define a DemoCharm with collect_unit_status

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

A charm class implementation that observes collect_unit_status and interacts with a workload container.

```python
class DemoCharm(ops.CharmBase):
    """Manage the workload."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self.container = self.unit.get_container('my-container')
        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        framework.observe(
            self.on['get-value'].action, self._on_get_value_action
        )

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        """Report the status of the workload."""
        try:
            service = self.container.get_service('workload')
        except (ops.ModelError, ops.pebble.ConnectionError):
            event.add_status(ops.MaintenanceStatus('waiting for container'))
        else:
            if not service.is_running():
                event.add_status(ops.MaintenanceStatus('waiting for workload'))
        event.add_status(ops.ActiveStatus())

    ...  # _on_get_value_action is unchanged.
```

--------------------------------

### Retrieve and update a secret by label

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use the label to fetch the secret object and perform operations like updating content without needing the secret ID.

```python
    def _rotate_webserver_secret(self):
        secret = self.model.get_secret(label='secret-for-webserver-app')
        secret.set_content(...)  # pass a new revision payload, as before
```

--------------------------------

### Declare user secret configuration

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Define a configuration option of type secret in charmcraft.yaml to allow user-provided secrets.

```yaml
config:
  options:
    my-secret-option:
      type: secret
      description: URI of the user-provided secret.
```

--------------------------------

### ops.hookcmds.relation_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves relation settings for a specific relation, unit, or application.

```APIDOC
## ops.hookcmds.relation_get(id: int | None = None, *, endpoint: str | None = None, key: str | None = None, unit: str | None = None, app: bool = False)

### Description
Get relation settings. Note that `id` can only be `None` if the current hook is a relation event, in which case Juju will use the ID of the relation that triggered the event.

### Parameters
- **id** (int | None) - Optional - The ID of the relation to get data for, or None to get data for the relation that triggered the current hook.
- **endpoint** (str | None) - Optional - If provided together with `id`, the relation is identified to Juju as `endpoint:id`.
- **key** (str | None) - Optional - The specific key to get data for, or None to get all data.
- **unit** (str | None) - Optional - The unit to get data for, or None to get data for the unit that triggered the current hook.
- **app** (bool) - Optional - Get the relation data for the overall application, not just a unit.

### Response
- **Returns** (dict[str, str] | str) - The relation settings.
```

--------------------------------

### ops.hookcmds.relation_ids

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Lists all relation IDs for a given endpoint.

```APIDOC
## ops.hookcmds.relation_ids(name: str)

### Description
List all relation IDs for the given endpoint.

### Parameters
- **name** (str) - Required - The endpoint name.

### Response
- **Returns** (list[str]) - A list of relation IDs.
```

--------------------------------

### ops.hookcmds.secret_get

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves the content of a secret by ID or label.

```APIDOC
## ops.hookcmds.secret_get(*, id=None, label=None, refresh=False, peek=False)

### Description
Fetches the content of a secret. Either the ID or the label must be provided.

### Parameters
- **id** (str) - Optional - The ID of the secret to retrieve.
- **label** (str) - Optional - The label of the secret to retrieve.
- **refresh** (bool) - Optional - Get the latest revision and set it for subsequent calls.
- **peek** (bool) - Optional - Get the latest revision just for this call.

### Returns
- **dict[str, str]** - The secret content.
```

--------------------------------

### Add a labeled secret as an owner

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Assign a label when creating a new secret to simplify future retrieval and management.

```python
class MyDatabaseCharm(ops.CharmBase):
    ...  # as before

    def _on_database_relation_joined(self, event: ops.RelationJoinedEvent):
        content = {
            'username': 'admin',
            'password': 'admin',
        }
        secret = self.app.add_secret(content, label='secret-for-webserver-app')
        secret.grant(event.relation)
        event.relation.data[event.unit]['secret-id'] = secret.id
```

--------------------------------

### Verify unit status

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-unit-tests-from-harness.md

Check the unit status after the event handler execution.

```python
    ...
    assert state_out.unit_status == testing.ActiveStatus()
```

--------------------------------

### Discourse post body template

Source: https://github.com/canonical/operator/blob/main/HACKING.md

The template for the body content of the release announcement on Discourse.

```text
The main improvements in this release are ...

Read more in the [full release notes on GitHub](link to the GitHub release).
```

--------------------------------

### Mocking secret content in tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use testing.State to inject secrets into the test environment. The tracked_content argument is mandatory.

```python
state_in = testing.State(
    secrets={
        testing.Secret(
            tracked_content={'key': 'public'},
            latest_content={'key': 'public', 'cert': 'private'},
        )
    }
)
```

--------------------------------

### Remove a relation unit

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Demonstrates removing a unit from a relation and the subsequent requirement to manually trigger a relation_changed event.

```default
rel_id = harness.add_relation('db', 'postgresql')
harness.add_relation_unit(rel_id, 'postgresql/0')
...
harness.remove_relation_unit(rel_id, 'postgresql/0')
```

--------------------------------

### Declare a subordinate relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Defines a relation with container scope for subordinate charms.

```yaml
requires:
  log-forwarder:
    interface: rsyslog-forwarder
    scope: container
```

--------------------------------

### Retrieve the root span in a unit test

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Access the root span created by the ops framework from the trace_data attribute of the testing context.

```python
ctx = Context(YourCharm)
ctx.run(ctx.on.start(), State())
main_span = next(s for s in ctx.trace_data if s.name == 'ops.main')
```

--------------------------------

### Stream charm logs with juju debug-log

Source: https://github.com/canonical/operator/blob/main/docs/howto/debug-your-charm.md

Common flags for filtering and controlling the output of the juju debug-log command.

```shell
juju debug-log --replay                          # show full history, then tail
juju debug-log --replay --no-tail                # show full history, then exit
juju debug-log --level WARNING                   # only warnings and above
juju debug-log --include unit-myapp-0            # only logs from myapp/0
juju debug-log --include-module unit.myapp/0.juju-log  # only charm-level logs
```

--------------------------------

### Reusing and modifying State

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-unit-tests-for-a-charm.md

Create a new State object by copying and modifying data from a previous run's output.

```python
state_out = ctx.run(...)  # The State we want to reuse.
relation = state_out.get_relation(...)  # A relation we want to modify.

# Copy and modify the relation data.
new_local_app_data = relation.local_app_data.copy()
new_local_app_data['foo'] = 'bar'

# Create a new State.
new_relation = dataclasses.replace(relation, local_app_data=new_local_app_data)
new_state = dataclasses.replace(state_out, relations={new_relation})
```

--------------------------------

### evaluate_status()

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Triggers status collection events to update unit and application status.

```APIDOC
## evaluate_status()

### Description
Trigger the collect-status events and set application and/or unit status. This method resets added statuses before triggering each collect-status event.
```

--------------------------------

### Accessing Action Event ID

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-actions.md

Use the .id attribute of the action event to generate unique identifiers for tasks like logging or temporary file creation.

```python
def _on_snapshot_action(self, event: ops.ActionEvent):
    temp_filename = f'backup-{event.id}.tar.gz'
    logger.info(
        'Using %s as the temporary backup filename in task %s',
        filename,
        event.id,
    )
    self.create_backup(temp_filename)
    ...
```

--------------------------------

### Verify span parent-child relationship

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Validate that one span is the direct parent of another by comparing the context and parent attributes.

```python
span_a = ...
span_b = ...
assert span_a.context is span_b.parent
```

--------------------------------

### Define interface tester fixture

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-interfaces.md

Configure the pytest fixture to provide the charm type and state template for interface tests.

```python
import pytest
from charm import MyFancyDatabaseCharm
from interface_tester import InterfaceTester
from scenario.state import State


@pytest.fixture
def interface_tester(interface_tester: InterfaceTester):
    interface_tester.configure(
        charm_type=MyFancyDatabaseCharm,
        state_template=State(
            leader=True,  # we need leadership
        ),
    )
    # this fixture needs to yield (NOT RETURN!) interface_tester again
    yield interface_tester
```

--------------------------------

### Handle heavy responses with check status

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-containers/manage-pebble-health-checks.md

Check the current status via the info property when performing heavy operations to ensure the response matches the current state.

```python
class PostgresCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        # Note that "db" is the workload container's name
        framework.observe(
            self.on['db'].pebble_check_failed, self._on_pebble_check_failed
        )
        framework.observe(
            self.on['db'].pebble_check_recovered,
            self._on_pebble_check_recovered,
        )

    def _on_pebble_check_failed(self, event: ops.PebbleCheckFailedEvent):
        if event.info.name != 'up':
            # For now, we ignore the other tests.
            return
        if event.info.status == ops.pebble.CheckStatus.DOWN:
            self.activate_alternative_configuration()
        else:
            self.activate_main_configuration()
```

--------------------------------

### Discourse post title format

Source: https://github.com/canonical/operator/blob/main/HACKING.md

The required format for the release announcement title on Discourse.

```text
Ops x.y.z released
```

--------------------------------

### Create a new secret revision

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Updating secret content by creating a new revision, which triggers a secret-changed event for observers.

```python
class MyDatabaseCharm(ops.CharmBase):
    ...  # as before

    def _rotate_webserver_secret(self, secret):
        content = secret.get_content()
        secret.set_content({
            'username': content['username'],  # keep the same username
            'password': _generate_new_secure_password(),  # something stronger than 'admin'
        })
```

--------------------------------

### Custom Wait Condition

Source: https://github.com/canonical/operator/blob/main/docs/howto/migrate/migrate-integration-tests-from-pytest-operator.md

Compose multiple checks using a lambda function within juju.wait.

```python
juju.wait(
    lambda status: (
        jubilant.all_active(status, 'mysql', 'redis')
        and jubilant.all_blocked(status, 'logger'),
    ),
)
```

--------------------------------

### replace_identities(identities: Mapping[str, IdentityDict | Identity | None]) -> None

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Replace the named identities in Pebble with the given ones.

```APIDOC
## replace_identities(identities)

### Description
Replace the named identities in Pebble with the given ones. Add those identities if they don't exist, or remove them if the dict value is None. Added in Juju version 3.6.4.

### Parameters
- **identities** (Mapping) - Required - A dict mapping identity names to dicts or Identity objects.
```

--------------------------------

### ops.hookcmds.secret_add

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Adds a new secret to the Juju environment.

```APIDOC
## ops.hookcmds.secret_add(content, *, label=None, description=None, expire=None, rotate=None, owner='application')

### Description
Adds a new secret with the specified content and configuration.

### Parameters
- **content** (dict[str, str]) - Required - The content of the secret.
- **label** (str) - Optional - A label used to identify the secret in hooks.
- **description** (str) - Optional - The secret description.
- **expire** (datetime | str) - Optional - Either a duration or time when the secret should expire.
- **rotate** (Literal) - Optional - The secret rotation policy ('never', 'hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly').
- **owner** (Literal) - Optional - The owner of the secret ('application' or 'unit').

### Returns
- **str** - The ID of the created secret.
```

--------------------------------

### remove_storage(storage_id: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Detaches a storage device in the testing backend.

```APIDOC
## remove_storage(storage_id: str)

### Description
Detach a storage device. Simulates a `juju remove-storage` call.

### Parameters
- **storage_id** (str) - Required - The full storage ID of the storage unit being removed.

### Raises
- **RuntimeError** - if the storage is not in the metadata.
```

--------------------------------

### Declare a requires relation in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Defines a requester endpoint with a limit on the number of relations.

```yaml
requires:
  db:
    interface: postgresql
    limit: 1
```

--------------------------------

### Handle relation-departed event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Define the event handler to perform cleanup when a specific unit departs the relation.

```python
def _on_smtp_relation_departed(self, event: ops.RelationDepartedEvent):
    if self.unit != event.departing_unit:
        self.remove_smtp_user(event.unit.name)
```

--------------------------------

### Retrieve relation objects

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Access relation objects using Model.get_relation for single endpoints or Model.relations for multiple endpoints.

```python
rel = self.model.get_relation("db")
if not rel:
    # Handle the case where the relation does not yet exist.
```

```python
for rel in self.model.relations.get('smtp', ()):
    # Do something with the relation object.
```

--------------------------------

### Define relation data schema

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Use a Pydantic model to define the structure of the data stored in the relation databag.

```python
class DatabaseProviderAppData(pydantic.BaseModel):
    credentials: str | None = pydantic.Field(
        default=None, description='A Juju secret ID'
    )
```

--------------------------------

### Report unit status via collect_unit_status

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-and-structure-charm-code.md

Observe the collect_unit_status event to report unit status at the end of each hook. Ops automatically selects the highest priority status if multiple are added.

```python
class DemoServerCharm(ops.CharmBase):
    """Manage the server."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        # Observe other events...

    def _on_collect_status(self, event: ops.CollectStatusEvent):
        if 'port' not in self.config:
            event.add_status(ops.BlockedStatus('no port specified'))
            return
        event.add_status(ops.ActiveStatus())
```

--------------------------------

### ops.hookcmds.secret_set

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Updates an existing secret.

```APIDOC
## ops.hookcmds.secret_set(id, *, content=None, label=None, description=None, expire=None, rotate=None, owner='application')

### Description
Updates the configuration or content of an existing secret.

### Parameters
- **id** (str) - Required - The ID of the secret.
- **content** (dict[str, str]) - Optional - The new content.
- **label** (str) - Optional - The new label.
- **description** (str) - Optional - The new description.
- **expire** (datetime | str) - Optional - The new expiration.
- **rotate** (Literal) - Optional - The new rotation policy.
- **owner** (Literal) - Optional - The new owner.
```

--------------------------------

### Disambiguate spans by instrumentation scope

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Filter or verify spans based on their instrumentation scope name to distinguish between framework and custom spans.

```python
# Spans from Ops
ops_span.instrumentation_scope.name == 'ops'
ops_span.name == ...

# tracer = opentelemetry.trace.get_tracer("my-charm")
my_span.instrumentation_scope.name == 'my-charm'
my_span.name == ...
```

--------------------------------

### Handle relation-broken event

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Define the event handler to perform cleanup when the entire relation is broken, typically restricted to the leader unit.

```python
def _on_db_relation_broken(self, event: ops.RelationBrokenEvent):
    if not self.is_leader():
        return
    self.drop_database(event.app.name)
```

--------------------------------

### Retrieve leader unit in integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-leadership-changes.md

Utility function to identify the current leader unit from the Juju status object.

```python
def get_leader_unit(juju: jubilant.Juju) -> str | None:
    """Utility method to get the name of the current leader."""
    for unit_name, unit in juju.status().apps['your-app'].units.items():
        if unit.leader:
            return unit_name
    # It's possible that no leader has been elected,
    # for example if the application has just been deployed.
    return None
```

--------------------------------

### Override test timeout

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Increase the wait timeout for the database integration test if it fails due to network or performance constraints.

```python
    juju.wait(jubilant.all_active, timeout=10 * 60)
```

--------------------------------

### Declare a peer relation

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Use PeerRelation for relations within the same application, omitting remote app data.

```python
relation = testing.PeerRelation(
    endpoint='peers',
    peers_data={1: {}, 2: {}, 42: {'foo': 'bar'}},
)
```

--------------------------------

### Filter Juju debug logs

Source: https://github.com/canonical/operator/blob/main/docs/howto/log-from-your-charm.md

Use the juju debug-log command with specific modules to isolate logs related to your charm and the uniter operation.

```text
juju debug-log --debug --include-module juju.worker.uniter.operation --include-module unit.<charm name>/<unit number>.juju-log
```

--------------------------------

### grant_secret(secret_id: str, observer: str | Application | Unit)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Grants read access to a secret for the given observer application or unit.

```APIDOC
## grant_secret(secret_id: str, observer: str | Application | Unit)

### Description
Grant read access to this secret for the given observer application or unit. Simulates the juju grant-secret command.

### Parameters
- **secret_id** (str) - Required - The ID of the secret to grant access to.
- **observer** (str | Application | Unit) - Required - The name of the application or specific unit to grant access to.
```

--------------------------------

### Define collect-unit-status handler

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Implement the handler method to evaluate various conditions and add appropriate statuses to the event.

```python
def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
    try:
        self.load_config(FastAPIConfig)
    except ValueError as e:
        event.add_status(ops.BlockedStatus(str(e)))
    if not self.model.get_relation("database"):
        # We need the user to do 'juju integrate'.
        event.add_status(ops.BlockedStatus("Waiting for database relation"))
    elif not self.database.fetch_relation_data():
        # We need the charms to finish integrating.
        event.add_status(ops.WaitingStatus("Waiting for database relation"))
    try:
        status = self.container.get_service(self.pebble_service_name)
    except (ops.pebble.APIError, ops.pebble.ConnectionError, ops.ModelError):
        event.add_status(ops.MaintenanceStatus("Waiting for Pebble in workload container"))
    else:
        if not status.is_running():
            event.add_status(ops.MaintenanceStatus("Waiting for the service to start up"))
    # If nothing is wrong, then the status is active.
    event.add_status(ops.ActiveStatus())
```

--------------------------------

### Declare a subordinate charm in charmcraft.yaml

Source: https://github.com/canonical/operator/blob/main/docs/explanation/subordinate-charms.md

Set the subordinate property to true to define the charm as a subordinate type.

```yaml
subordinate: true
```

--------------------------------

### ops.testing.ActionFailed

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

An exception class raised when event.fail() is invoked during an action handler execution within the testing framework.

```APIDOC
## class ops.testing.ActionFailed

### Description
Exception raised when `event.fail()` is called during an action handler. This allows tests to capture and inspect failure messages, logs, and the resulting state.

### Attributes
- **message** (str) - Optional details of the failure.
- **output** (ActionOutput) - Any logs and results set by the Charm.
- **state** (State | None) - The Juju state after the action has been run.
```

--------------------------------

### Modify frozen dataclasses with replace

Source: https://github.com/canonical/operator/blob/main/docs/explanation/state-transition-testing.md

Use the dataclasses replace API to create modified copies of immutable state objects.

```python
import dataclasses

relation = testing.Relation('foo', remote_app_data={'1': '2'})
# make a copy of relation, but with remote_app_data set to {'3': '4'}
relation2 = dataclasses.replace(relation, remote_app_data={'3': '4'})
```

--------------------------------

### get_secret_grants(secret_id: str, relation_id: int) -> set[str]

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Returns the set of app and unit names granted to a secret for a specific relation.

```APIDOC
## get_secret_grants(secret_id: str, relation_id: int) -> set[str]

### Description
Return the set of app and unit names granted to secret for this relation.

### Parameters
- **secret_id** (str) - Required - The ID of the secret to get grants for.
- **relation_id** (int) - Required - The ID of the relation granted access.

### Returns
- **set[str]** - A set of application and unit names.
```

--------------------------------

### Compare enum values by identity

Source: https://github.com/canonical/operator/blob/main/STYLE.md

Use 'is' or 'is not' for comparing enum values to follow standard Python enum practices.

```python
if status == pebble.ServiceStatus.ACTIVE:
    print('Running')

if status != pebble.ServiceStatus.ACTIVE:
    print('Stopped')
```

```python
if status is pebble.ServiceStatus.ACTIVE:
    print('Running')

if status is not pebble.ServiceStatus.ACTIVE:
    print('Stopped')
```

--------------------------------

### Avoid nested comprehensions and generator expressions

Source: https://github.com/canonical/operator/blob/main/STYLE.md

Prefer flat loops over nested comprehensions to improve readability.

```python
units = [units for app in model.apps for unit in app.units]

for current in (
    status for status in pebble.ServiceStatus if status is not pebble.ServiceStatus.ACTIVE
):
    ...
```

```python
units = []
for app in model.apps:
    for unit in app.units:
        units.append(unit)

for status in pebble.ServiceStatus:
    if status is pebble.ServiceStatus.ACTIVE:
        continue
    ...
```

--------------------------------

### Read and Write StoredState in Event Handlers

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-stored-state.md

Access and modify stored state attributes within event handler methods to persist data across Juju events.

```python
def _on_start(self, event: ops.StartEvent):
    if self._stored.expensive_value is None:
        self._stored.expensive_value = self._calculate_expensive_value()


def _on_install(self, event: ops.InstallEvent):
    # We can use self._stored.expensive_value here, and it will have the value
    # set in the start event.
    logger.info('Current value: %s', self._stored.expensive_value)
```

--------------------------------

### Override log file per session

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Specify unique log files for individual pytest invocations.

```default
pytest --log-file "run1.log" ...
pytest --log-file "run2.log" ...
```

--------------------------------

### Define COS Lite Juju fixture

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/observe-your-charm-with-cos-lite.md

Fixture to create a separate Juju model for COS Lite deployment.

```python
@pytest.fixture(scope="module")
def cos(juju_factory: pytest_jubilant.JujuFactory):
    yield juju_factory.get_juju(suffix="cos")
```

--------------------------------

### ops.hookcmds.secret_ids

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Retrieves all secret IDs owned by the application.

```APIDOC
## ops.hookcmds.secret_ids()

### Description
Returns a list of IDs for all secrets owned by the application.

### Returns
- **list[str]** - A list of secret IDs.
```

--------------------------------

### Read data from various relation databags

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Access remote, peer, or local databags using the .data attribute on the relation object.

```python
def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
    remote_units_databags = {
        event.relation.data[unit]
        for unit in event.relation.units
        if unit.app is not self.app
    }
```

```python
def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
    peer_units_databags = {
        event.relation.data[unit]
        for unit in event.relation.units
        if unit.app is self.app
    }
```

```python
def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
    remote_app_databag = event.relation.data[relation.app]
```

```python
def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
    local_app_databag = event.relation.data[self.app]
```

```python
def _on_database_relation_changed(self, event: ops.RelationChangedEvent):
    local_unit_databag = event.relation.data[self.unit]
```

--------------------------------

### Verify span ancestry

Source: https://github.com/canonical/operator/blob/main/docs/howto/trace-your-charm.md

Check if a span is an ancestor of another by traversing the span hierarchy using the trace_data.

```python
spans_by_id = {s.context.span_id: s for s in ctx.trace_data}


def ancestors(span: ReadableSpan) -> Generator[ReadableSpan]:
    while span.parent:
        span = spans_by_id[span.parent.span_id]
        yield span


assert span_a in list(ancestors(span_c))
```

--------------------------------

### Filter integration tests

Source: https://github.com/canonical/operator/blob/main/docs/howto/write-integration-tests-for-a-charm.md

Run a specific subset of tests using pytest expressions.

```text
tox -e integration -- tests/integration/test_charm.py -k "not test_one"
```

--------------------------------

### Document Juju version additions in MyST Markdown

Source: https://github.com/canonical/operator/blob/main/CONTRIBUTING.md

Syntax for marking features added in specific Juju versions within MyST Markdown files.

```markdown
```{jujuadded} x.y
Summary
```
```

--------------------------------

### trigger_secret_rotation(secret_id: str, *, label: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Triggers a secret-rotate event for a specific secret manually within the harness.

```APIDOC
## trigger_secret_rotation(secret_id: str, *, label: str | None = None)

### Description
Trigger a secret-rotate event for the given secret. This fires the event manually as time-based events cannot be simulated in the harness.

### Parameters
- **secret_id** (str) - Required - The ID of the secret associated with the event.
- **label** (str | None) - Optional - Label value to send to the event. If None, the secret’s label is used.
```

--------------------------------

### Update Secret definitions

Source: https://github.com/canonical/operator/blob/main/testing/UPGRADING.md

Secrets now require only tracked and latest content, removing the need for IDs and full revision dictionaries.

```python
# Older Scenario code.
state = State(
    secrets=[
        scenario.Secret(id='foo', contents={0: {'certificate': 'xxxx'}}),
        scenario.Secret(
            id='foo',
            contents={
                0: {'password': '1234'},
                1: {'password': 'abcd'},
                2: {'password': 'admin'},
            },
        ),
    ]
)

# Scenario 7.x
state = State(
    secrets={
        scenario.Secret({'certificate': 'xxxx'}),
        scenario.Secret(
            tracked_content={'password': '1234'},
            latest_content={'password': 'admin'},
        ),
    }
)
```

--------------------------------

### add_user_secret

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Adds a secret owned by the user, simulating the juju add-secret command.

```APIDOC
## add_user_secret(content: dict[str, str])

### Description
Add a secret owned by the user, simulating the juju add-secret command.

### Parameters
- **content** (dict[str, str]) - Required - A key-value mapping containing the payload of the secret.

### Returns
- **str** - The ID of the newly-added secret.
```

--------------------------------

### update_relation_data(relation_id: int, app_or_unit: str, key_values: Mapping[str, str])

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Updates relation data for a unit or application and triggers a relation_changed event.

```APIDOC
## update_relation_data(relation_id: int, app_or_unit: str, key_values: Mapping[str, str])

### Description
Update the relation data for a given unit or application in a given relation. This also triggers the relation_changed event for the given relation_id.

### Parameters
- **relation_id** (int) - Required - The integer relation ID representing this relation.
- **app_or_unit** (str) - Required - The unit or application name that is being updated.
- **key_values** (Mapping) - Required - Each key/value will be updated in the relation data.
```

--------------------------------

### add_relation_unit

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Adds a new unit to an existing relation, triggering a relation_joined event.

```APIDOC
## add_relation_unit(relation_id: int, remote_unit_name: str)

### Description
Adds a new unit to a relation. This will trigger a relation_joined event.

### Parameters
- **relation_id** (int) - Required - The integer relation identifier.
- **remote_unit_name** (str) - Required - A string representing the remote unit that is being added.
```

--------------------------------

### Remove all secret revisions

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Call remove_all_revisions on a secret object to destroy it entirely.

```python
class MyDatabaseCharm(ops.CharmBase):
    ...

    # called from an event handler
    def _remove_webserver_secret(self):
        secret = self.model.get_secret(label='secret-for-webserver-app')
        secret.remove_all_revisions()
```

--------------------------------

### ops.hookcmds.relation_set

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Sets relation settings for a specific relation.

```APIDOC
## ops.hookcmds.relation_set(data: Mapping[str, str], id: int | None = None, *, endpoint: str | None = None, app: bool = False)

### Description
Set relation settings. Setting the value for a key to the empty string deletes that key.

### Parameters
- **data** (Mapping[str, str]) - Required - The relation data to set.
- **id** (int | None) - Optional - The ID of the relation to set data for, or None to set data for the relation that triggered the current hook.
- **endpoint** (str | None) - Optional - If provided together with `id`, the relation is identified to Juju as `endpoint:id`.
- **app** (bool) - Optional - Set data for the overall application, not just a unit.
```

--------------------------------

### set_secret_content(secret_id: str, content: dict[str, str])

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Updates a secret's content and triggers a secret-changed event.

```APIDOC
## set_secret_content(secret_id: str, content: dict[str, str])

### Description
Updates a secret’s content, adds a new revision, and fires the secret-changed event.

### Parameters
- **secret_id** (str) - Required - The ID of the secret to update.
- **content** (dict[str, str]) - Required - A key-value mapping containing the new payload.
```

--------------------------------

### ops.hookcmds.close_port

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Registers a request to close a port or port range.

```APIDOC
## ops.hookcmds.close_port(protocol: str | None = None, port: int | None = None, *, to_port: int | None = None, endpoints: str | Iterable[str] | None = None)

### Description
Register a request to close a port or port range.

### Parameters
- **protocol** (str) - Optional
- **port** (int) - Optional
- **to_port** (int) - Optional
- **endpoints** (str | Iterable[str]) - Optional
```

--------------------------------

### Update pebble layer test assertion

Source: https://github.com/canonical/operator/blob/main/docs/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/integrate-your-charm-with-postgresql.md

Updates the existing pebble layer test to expect a blocked status when no database relation is present.

```python
    # Check the unit is blocked:
    assert state_out.unit_status == testing.BlockedStatus("Waiting for database relation")
```

--------------------------------

### ops.hookcmds.secret_remove

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Removes a secret from the environment.

```APIDOC
## ops.hookcmds.secret_remove(id, *, revision=None)

### Description
Removes an existing secret. If revision is not provided, all revisions are removed.

### Parameters
- **id** (str) - Required - The ID of the secret.
- **revision** (int) - Optional - The specific revision to remove.
```

--------------------------------

### ops.hookcmds.secret_revoke

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Revokes access to a secret.

```APIDOC
## ops.hookcmds.secret_revoke(id, *, relation_id=None, app=None, unit=None)

### Description
Revokes access to a secret for a specific relation, application, or unit.

### Parameters
- **id** (str) - Required - The ID of the secret.
- **relation_id** (int) - Optional - The relation ID.
- **app** (str) - Optional - Revoke access from all units in the application.
- **unit** (str) - Optional - Revoke access from a specific unit.
```

--------------------------------

### stop_checks(*check_names)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing.rst

Stop given check(s) by name.

```APIDOC
## stop_checks(*check_names: str) -> list[str]

### Description
Stop given check(s) by name. Returns a list of check names that were stopped.
```

--------------------------------

### ops.hookcmds.secret_grant

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-hookcmds.rst

Grants access to a secret for a specific relation.

```APIDOC
## ops.hookcmds.secret_grant(id, relation_id, *, unit=None)

### Description
Grants access to a secret to a specific relation, optionally restricted to a unit.

### Parameters
- **id** (str) - Required - The ID of the secret.
- **relation_id** (int) - Required - The relation ID.
- **unit** (str) - Optional - Limit access to this specific unit.
```

--------------------------------

### trigger_secret_expiration(secret_id: str, revision: int, *, label: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Manually triggers a secret-expired event for a specific secret.

```APIDOC
## trigger_secret_expiration(secret_id: str, revision: int, *, label: str | None = None)

### Description
Triggers a secret-expired event for the given secret. This is used to simulate time-based expiration events.

### Parameters
- **secret_id** (str) - Required - The ID of the secret associated with the event.
- **revision** (int) - Required - The revision number to provide to the event.
- **label** (str) - Optional - The label value to send to the event.
```

--------------------------------

### trigger_secret_removal(secret_id: str, revision: int, *, label: str | None = None)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Triggers a secret-remove event for a specific secret and revision manually within the harness.

```APIDOC
## trigger_secret_removal(secret_id: str, revision: int, *, label: str | None = None)

### Description
Trigger a secret-remove event for the given secret and revision. This method allows manual firing of the event typically managed by Juju.

### Parameters
- **secret_id** (str) - Required - The ID of the secret associated with the event.
- **revision** (int) - Required - Revision number to provide to the event.
- **label** (str | None) - Optional - Label value to send to the event. If None, the secret’s label is used.
```

--------------------------------

### Revoke secret access

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Use the revoke method on a secret object to remove access for a specific relation.

```python
class MyDatabaseCharm(ops.CharmBase):
    ...  # as before

    # called from an event handler
    def _revoke_webserver_secret_access(self, relation):
        secret = self.model.get_secret(label='secret-for-webserver-app')
        secret.revoke(relation)
```

--------------------------------

### get_secret_revisions(secret_id: str) -> list[int]

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Returns the list of revision IDs for a given secret.

```APIDOC
## get_secret_revisions(secret_id: str) -> list[int]

### Description
Return the list of revision IDs for the given secret, oldest first.

### Parameters
- **secret_id** (str) - Required - The ID of the secret to get revisions for.

### Returns
- **list[int]** - A list of revision IDs.
```

--------------------------------

### add_model_secret

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Adds a secret to the simulated model owned by a remote application or unit.

```APIDOC
## add_model_secret(owner, content)

### Description
Adds a secret owned by the remote application or unit specified in the test model.

### Parameters
- **owner** (str | Application | Unit) - Required - The name of the remote application or unit that will own the secret.
- **content** (dict[str, str]) - Required - A key-value mapping containing the payload of the secret.

### Returns
- **str** - The ID of the newly added secret.
```

--------------------------------

### remove_identities(identities: Iterable[str]) -> None

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Remove the named identities in Pebble.

```APIDOC
## remove_identities(identities)

### Description
Remove the named identities in Pebble. Added in Juju version 3.6.4.

### Parameters
- **identities** (Iterable[str]) - Required - A set of identity names to remove.
```

--------------------------------

### revoke_secret(secret_id: str, observer: str | Application | Unit)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Revokes read access to a secret for a given observer.

```APIDOC
## revoke_secret(secret_id: str, observer: str | Application | Unit)

### Description
Revoke read access to this secret for the given observer application or unit.

### Parameters
- **secret_id** (str) - Required - The ID of the secret to revoke access for.
- **observer** (str | Application | Unit) - Required - The name of the application or specific unit to revoke access to.
```

--------------------------------

### Declare a subordinate relation

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-relations.md

Use SubordinateRelation for relations that always involve exactly one remote unit.

```python
relation = testing.SubordinateRelation(
    endpoint='peers',
    remote_unit_data={'foo': 'bar'},
    remote_app_name='zookeeper',
    remote_unit_id=42,
)
relation.remote_unit_name  # 'zookeeper/42'
```

--------------------------------

### Remove a single secret revision

Source: https://github.com/canonical/operator/blob/main/docs/howto/manage-secrets.md

Implement a secret-remove handler to call remove_revision when a specific revision is no longer tracked.

```python
class MyDatabaseCharm(ops.CharmBase):
    ...  # as before

    def __init__(self, *args, **kwargs):
        ...  # other setup
        self.framework.observe(self.on.secret_remove, self._on_secret_remove)

    def _on_secret_remove(self, event: ops.SecretRemoveEvent):
        # All observers are done with this revision, remove it:
        event.remove_revision()
```

--------------------------------

### remove_relation_unit(relation_id: int, remote_unit_name: str)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Removes a specific unit from a relation.

```APIDOC
## remove_relation_unit(relation_id: int, remote_unit_name: str)

### Description
Remove a unit from a relation. This triggers a relation_departed event.

### Parameters
- **relation_id** (int) - Required - The integer relation identifier.
- **remote_unit_name** (str) - Required - A string representing the remote unit that is being removed.
```

--------------------------------

### stop_checks

Source: https://github.com/canonical/operator/blob/main/docs/reference/pebble.rst

Stops the specified health checks.

```APIDOC
## stop_checks(checks: Iterable[str]) -> list[str]

### Description
Stops the provided list of checks. Only checks that were active are returned.

### Parameters
- **checks** (Iterable[str]) - Required - Non-empty list of check names to stop.

### Returns
- **list[str]** - A set of check names that were successfully stopped.
```

--------------------------------

### remove_relation(relation_id: int)

Source: https://github.com/canonical/operator/blob/main/docs/reference/ops-testing-harness.rst

Removes a relation from the testing harness.

```APIDOC
## remove_relation(relation_id: int)

### Description
Remove a relation from the testing environment.

### Parameters
- **relation_id** (int) - Required - The relation ID for the relation to be removed.

### Raises
- **RelationNotFoundError** - if relation id is not valid
```