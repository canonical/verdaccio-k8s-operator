#!/usr/bin/env python3
"""Operate Verdaccio on Kubernetes."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import ops
from pydantic import BaseModel, ConfigDict, ValidationError

logger = logging.getLogger(__name__)

CONTAINER_NAME = "verdaccio"
SERVICE_NAME = "verdaccio"
PORT = 4873
CONFIG_PATH = "/verdaccio/conf/config.yaml"
COMMAND = f"verdaccio --config {CONFIG_PATH} --listen http://0.0.0.0:{PORT}"


class CharmConfig(BaseModel):
    """Validated operator configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    log_level: Literal["debug", "info", "warning", "error"] = "info"


@dataclass(frozen=True)
class ReconcilePlan:
    """Complete desired workload state."""

    config: str
    layer: ops.pebble.LayerDict


def config_input(config: Mapping[str, object]) -> dict[str, object]:
    """Adapt Juju configuration to the validation boundary."""
    return {"log_level": config.get("log-level", "info")}


def render_config(config: CharmConfig) -> str:
    """Serialize validated configuration as Verdaccio YAML."""
    return f"""storage: /verdaccio/storage
auth:
  htpasswd:
    file: /verdaccio/storage/htpasswd
uplinks:
  npmjs:
    url: https://registry.npmjs.org/
packages:
  '@*/*':
    access: $all
    publish: $authenticated
    unpublish: $authenticated
    proxy: npmjs
  '**':
    access: $all
    publish: $authenticated
    unpublish: $authenticated
    proxy: npmjs
middlewares:
  audit:
    enabled: true
log:
  type: stdout
  format: pretty
  level: {config.log_level}
"""


def build_plan(config: CharmConfig) -> ReconcilePlan:
    """Build the desired state without side effects."""
    layer: ops.pebble.LayerDict = {
        "summary": "Verdaccio",
        "description": "Pebble layer for Verdaccio",
        "services": {
            SERVICE_NAME: {
                "override": "replace",
                "summary": "Verdaccio npm registry",
                "command": COMMAND,
                "startup": "enabled",
                "user-id": 10001,
                "working-dir": "/opt/verdaccio",
                "environment": {"HOME": "/opt/verdaccio"},
            }
        },
    }
    return ReconcilePlan(config=render_config(config), layer=layer)


class VerdaccioK8SCharm(ops.CharmBase):
    """Operate a single Verdaccio workload container."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self.container = self.unit.get_container(CONTAINER_NAME)

        for event in (self.on.config_changed, self.on[CONTAINER_NAME].pebble_ready):
            framework.observe(event, self._reconcile)
        framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

    def _load_config(self) -> CharmConfig:
        """Read and validate the complete current configuration."""
        return CharmConfig.model_validate(config_input(self.config))

    def _reconcile(self, _: ops.EventBase) -> None:
        """Converge the workload from current authoritative state."""
        try:
            config = self._load_config()
        except ValidationError as error:
            fields = ", ".join(".".join(map(str, item["loc"])) for item in error.errors())
            self.unit.status = ops.BlockedStatus(f"Invalid configuration: {fields}")
            return

        if not self.container.can_connect():
            self.unit.status = ops.WaitingStatus("Waiting for Verdaccio container")
            return

        plan = build_plan(config)
        self.unit.status = ops.MaintenanceStatus("Reconciling Verdaccio")
        try:
            config_changed = self._sync_config(plan.config)
            service_changed = self._sync_service(plan.layer)
            self.unit.set_ports(PORT)

            if service_changed:
                self.container.replan()
            else:
                service = self.container.get_service(SERVICE_NAME)
                if config_changed and service.is_running():
                    self.container.restart(SERVICE_NAME)
                elif not service.is_running():
                    self.container.start(SERVICE_NAME)
        except (ops.ModelError, ops.pebble.APIError, ops.pebble.ConnectionError) as error:
            logger.info("Verdaccio container is not ready: %s", error)
            self.unit.status = ops.WaitingStatus("Waiting for Verdaccio container")

    def _sync_config(self, desired: str) -> bool:
        """Write configuration only when its content differs."""
        if self.container.exists(CONFIG_PATH):
            with self.container.pull(CONFIG_PATH) as stream:
                current = stream.read()
        else:
            current = None
        if current == desired:
            return False
        self.container.push(CONFIG_PATH, desired, make_dirs=True, permissions=0o644)
        return True

    def _sync_service(self, layer: ops.pebble.LayerDict) -> bool:
        """Update the Pebble service layer only when its plan differs."""
        service = self.container.get_plan().services.get(SERVICE_NAME)
        if (
            service is not None
            and service.command == COMMAND
            and service.startup is ops.pebble.ServiceStartup.ENABLED
            and service.user_id == 10001
            and service.working_dir == "/opt/verdaccio"
            and service.environment == {"HOME": "/opt/verdaccio"}
        ):
            return False
        self.container.add_layer(SERVICE_NAME, layer, combine=True)
        return True

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """Report status from validated config and current workload health."""
        try:
            self._load_config()
        except ValidationError:
            event.add_status(ops.BlockedStatus("Invalid configuration: log_level"))
            return

        if not self.container.can_connect():
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        try:
            service = self.container.get_service(SERVICE_NAME)
        except (ops.ModelError, ops.pebble.APIError, ops.pebble.ConnectionError):
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        if not service.is_running():
            event.add_status(ops.MaintenanceStatus("Waiting for Verdaccio service"))
            return
        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(VerdaccioK8SCharm)
