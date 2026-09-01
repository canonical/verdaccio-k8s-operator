"""Plan and apply Verdaccio workload state through Pebble."""

from dataclasses import dataclass

import ops

from configuration import CharmConfig

CONTAINER_NAME = "verdaccio"
SERVICE_NAME = "verdaccio"
CONFIG_PATH = "/verdaccio/conf/config.yaml"
WORKLOAD_USER_ID = 10001
WORKING_DIRECTORY = "/opt/verdaccio"


class WorkloadUnavailableError(Exception):
    """The workload container cannot currently satisfy an operation."""


@dataclass(frozen=True)
class WorkloadPlan:
    """Complete desired workload state."""

    config: str
    command: str
    layer: ops.pebble.LayerDict
    open_ports: frozenset[int]


def render_config(config: CharmConfig) -> str:
    """Serialize every validated Verdaccio option as workload YAML."""
    return config.verdaccio.as_yaml()


def build_command(config: CharmConfig) -> str:
    """Build the validated listener command owned by the charm."""
    address = (
        f"[{config.listen_address}]" if ":" in config.listen_address else config.listen_address
    )
    return (
        f"verdaccio --config {CONFIG_PATH} "
        f"--listen {config.listen_protocol}://{address}:{config.listen_port}"
    )


def build_plan(config: CharmConfig) -> WorkloadPlan:
    """Build the complete desired workload state without side effects."""
    command = build_command(config)
    layer: ops.pebble.LayerDict = {
        "summary": "Verdaccio",
        "description": "Pebble layer for Verdaccio",
        "services": {
            SERVICE_NAME: {
                "override": "replace",
                "summary": "Verdaccio npm registry",
                "command": command,
                "startup": "enabled",
                "user-id": WORKLOAD_USER_ID,
                "working-dir": WORKING_DIRECTORY,
                "environment": {"HOME": WORKING_DIRECTORY},
            }
        },
    }
    return WorkloadPlan(
        config=render_config(config),
        command=command,
        layer=layer,
        open_ports=frozenset({config.listen_port}),
    )


class VerdaccioWorkload:
    """Change-aware Pebble adapter for the Verdaccio container."""

    def __init__(self, container: ops.Container) -> None:
        self._container = container

    def can_connect(self) -> bool:
        """Return whether Pebble is currently reachable."""
        return self._container.can_connect()

    def apply(self, plan: WorkloadPlan) -> None:
        """Apply only differences between current and desired workload state."""
        try:
            config_changed = self._sync_config(plan.config)
            service_changed = self._sync_service(plan)

            if service_changed:
                self._container.replan()
                return

            service = self._container.get_service(SERVICE_NAME)
            if config_changed and service.is_running():
                self._container.restart(SERVICE_NAME)
            elif not service.is_running():
                self._container.start(SERVICE_NAME)
        except (ops.ModelError, ops.pebble.APIError, ops.pebble.ConnectionError) as error:
            raise WorkloadUnavailableError(str(error)) from error

    def is_running(self) -> bool:
        """Return whether the managed service is currently running."""
        try:
            return self._container.get_service(SERVICE_NAME).is_running()
        except (ops.ModelError, ops.pebble.APIError, ops.pebble.ConnectionError) as error:
            raise WorkloadUnavailableError(str(error)) from error

    def _sync_config(self, desired: str) -> bool:
        if self._container.exists(CONFIG_PATH):
            with self._container.pull(CONFIG_PATH) as stream:
                current = stream.read()
        else:
            current = None

        if current == desired:
            return False

        self._container.push(CONFIG_PATH, desired, make_dirs=True, permissions=0o644)
        return True

    def _sync_service(self, plan: WorkloadPlan) -> bool:
        service = self._container.get_plan().services.get(SERVICE_NAME)
        if (
            service is not None
            and service.command == plan.command
            and service.startup is ops.pebble.ServiceStartup.ENABLED
            and service.user_id == WORKLOAD_USER_ID
            and service.working_dir == WORKING_DIRECTORY
            and service.environment == {"HOME": WORKING_DIRECTORY}
        ):
            return False

        self._container.add_layer(SERVICE_NAME, plan.layer, combine=True)
        return True
