"""Plan and apply Verdaccio workload state through Pebble."""

from dataclasses import dataclass
from urllib.parse import urlsplit

import ops

from configuration import CharmConfig, TracingConfig

CONTAINER_NAME = "verdaccio"
SERVICE_NAME = "verdaccio"
HEALTH_CHECK_NAME = "verdaccio-ready"
HEALTH_CHECK_PATH = "/-/ping"
CONFIG_PATH = "/verdaccio/conf/config.yaml"
WORKLOAD_USER_ID = 584792
WORKING_DIRECTORY = "/opt/verdaccio"
INSTRUMENTATION_PATH = "/opt/verdaccio-app/dist/instrumentation.js"
METRICS_PATH = "/metrics"
METRICS_PORT = 9464


class WorkloadUnavailableError(Exception):
    """The workload container cannot currently satisfy an operation."""


@dataclass(frozen=True)
class WorkloadPlan:
    """Complete desired workload state."""

    config: str
    layer: ops.pebble.Layer
    open_ports: frozenset[int]


def _workload_settings(
    config: CharmConfig,
    ingress_url: str | None,
    tracing: TracingConfig | None,
    service_name: str,
) -> tuple[str, dict[str, str]]:
    """Build the complete charm-owned workload configuration and environment."""
    environment = {
        "HOME": WORKING_DIRECTORY,
        "NODE_OPTIONS": f"--require {INSTRUMENTATION_PATH}",
        "OTEL_SERVICE_NAME": service_name,
        "VERDACCIO_METRICS_PORT": str(METRICS_PORT),
    }
    if tracing is not None:
        environment.update(tracing.as_environment())

    verdaccio = config.verdaccio
    if ingress_url is not None:
        parsed_url = urlsplit(ingress_url)
        ingress_path = parsed_url.path.strip("/")
        url_prefix = f"/{ingress_path}" if ingress_path else None
        verdaccio = verdaccio.model_copy(update={"url_prefix": url_prefix})
        environment["VERDACCIO_PUBLIC_URL"] = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return verdaccio.as_yaml(), environment


def build_command(config: CharmConfig) -> str:
    """Build the validated listener command owned by the charm."""
    address = (
        f"[{config.listen_address}]" if ":" in config.listen_address else config.listen_address
    )
    return (
        f"verdaccio --config {CONFIG_PATH} "
        f"--listen {config.listen_protocol}://{address}:{config.listen_port}"
    )


def _health_check_host(address: str) -> str:
    """Resolve a wildcard listener to a container-local health-check host."""
    if address == "0.0.0.0":
        return "127.0.0.1"
    if address == "::":
        return "::1"
    return address


def build_health_check_url(config: CharmConfig) -> str:
    """Build the container-local URL for Verdaccio's registry-root ping endpoint."""
    address = _health_check_host(config.listen_address)
    if ":" in address:
        address = f"[{address}]"
    return f"http://{address}:{config.listen_port}{HEALTH_CHECK_PATH}"


def build_plan(
    config: CharmConfig,
    *,
    service_name: str,
    ingress_url: str | None = None,
    tracing: TracingConfig | None = None,
) -> WorkloadPlan:
    """Build the complete desired workload state without side effects."""
    check: ops.pebble.CheckDict = {
        "override": "replace",
        "level": "ready",
        "period": "10s",
        "timeout": "3s",
        "threshold": 3,
    }
    if config.listen_protocol == "https":
        check["tcp"] = {
            "host": _health_check_host(config.listen_address),
            "port": config.listen_port,
        }
    else:
        check["http"] = {"url": build_health_check_url(config)}

    rendered_config, environment = _workload_settings(config, ingress_url, tracing, service_name)
    layer_config: ops.pebble.LayerDict = {
        "summary": "Verdaccio",
        "description": "Pebble layer for Verdaccio",
        "services": {
            SERVICE_NAME: {
                "override": "replace",
                "summary": "Verdaccio npm registry",
                "command": build_command(config),
                "startup": "enabled",
                "user-id": WORKLOAD_USER_ID,
                "working-dir": WORKING_DIRECTORY,
                "environment": environment,
            }
        },
        "checks": {HEALTH_CHECK_NAME: check},
    }
    return WorkloadPlan(
        config=rendered_config,
        layer=ops.pebble.Layer(layer_config),
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
            service_changed, check_changed = self._sync_layer(plan)

            if service_changed:
                self._container.replan()
                return
            if check_changed:
                self._container.replan()

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

    def is_healthy(self) -> bool:
        """Return whether Pebble's Verdaccio health check is passing."""
        try:
            check = self._container.get_check(HEALTH_CHECK_NAME)
            return check.status is ops.pebble.CheckStatus.UP
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

    def _sync_layer(self, plan: WorkloadPlan) -> tuple[bool, bool]:
        current_plan = self._container.get_plan()
        service_changed = (
            current_plan.services.get(SERVICE_NAME) != plan.layer.services[SERVICE_NAME]
        )
        check_changed = (
            current_plan.checks.get(HEALTH_CHECK_NAME) != plan.layer.checks[HEALTH_CHECK_NAME]
        )
        if not service_changed and not check_changed:
            return False, False

        self._container.add_layer(SERVICE_NAME, plan.layer, combine=True)
        return service_changed, check_changed
