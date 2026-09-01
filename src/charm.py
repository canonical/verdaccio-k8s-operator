#!/usr/bin/env python3
"""Orchestrate Verdaccio reconciliation events and status."""

import logging

import ops
from pydantic import ValidationError

from configuration import load_config, validation_error_message
from workload import CONTAINER_NAME, VerdaccioWorkload, WorkloadUnavailableError, build_plan

logger = logging.getLogger(__name__)


class VerdaccioK8SCharm(ops.CharmBase):
    """Operate a single Verdaccio workload container."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        container = self.unit.get_container(CONTAINER_NAME)
        self._workload = VerdaccioWorkload(container)

        for event in (self.on.config_changed, self.on[CONTAINER_NAME].pebble_ready):
            framework.observe(event, self._reconcile)
        framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

    def _reconcile(self, _: ops.EventBase) -> None:
        """Read, validate, plan, and apply the complete desired state."""
        try:
            config = load_config(self.config)
        except ValidationError as error:
            self.unit.status = ops.BlockedStatus(validation_error_message(error))
            return

        if not self._workload.can_connect():
            self.unit.status = ops.WaitingStatus("Waiting for Verdaccio container")
            return

        plan = build_plan(config)
        self.unit.status = ops.MaintenanceStatus("Reconciling Verdaccio")
        try:
            self._workload.apply(plan)
            self.unit.set_ports(*plan.open_ports)
        except WorkloadUnavailableError as error:
            logger.info("Verdaccio container is not ready: %s", error)
            self.unit.status = ops.WaitingStatus("Waiting for Verdaccio container")

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """Report status from current validated inputs and workload health."""
        try:
            load_config(self.config)
        except ValidationError as error:
            event.add_status(ops.BlockedStatus(validation_error_message(error)))
            return

        if not self._workload.can_connect():
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        try:
            running = self._workload.is_running()
        except WorkloadUnavailableError:
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        if not running:
            event.add_status(ops.MaintenanceStatus("Waiting for Verdaccio service"))
            return

        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(VerdaccioK8SCharm)
