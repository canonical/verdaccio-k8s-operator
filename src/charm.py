#!/usr/bin/env python3
"""Orchestrate Verdaccio reconciliation events and status."""

import logging

import ops
from charms.loki_k8s.v1.loki_push_api import LogForwarder
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.tempo_coordinator_k8s.v0.tracing import (
    ProtocolNotRequestedError,
    TracingEndpointRequirer,
)
from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from pydantic import ValidationError

from configuration import (
    TracingConfig,
    load_config,
    load_tracing_config,
    tracing_validation_error_message,
    validation_error_message,
)
from workload import (
    CONTAINER_NAME,
    METRICS_PATH,
    METRICS_PORT,
    VerdaccioWorkload,
    WorkloadUnavailableError,
    build_plan,
)

logger = logging.getLogger(__name__)
STORAGE_NAME = "data"


class VerdaccioK8SCharm(ops.CharmBase):
    """Operate a single Verdaccio workload container."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        container = self.unit.get_container(CONTAINER_NAME)
        self._workload = VerdaccioWorkload(container)
        self._ingress = IngressPerAppRequirer(self, strip_prefix=True)
        self._logging = LogForwarder(self, relation_name="logging")
        self._metrics = MetricsEndpointProvider(
            self,
            relation_name="metrics-endpoint",
            jobs=[
                {
                    "metrics_path": METRICS_PATH,
                    "static_configs": [{"targets": [f"*:{METRICS_PORT}"]}],
                }
            ],
        )
        self._tracing = TracingEndpointRequirer(
            self,
            relation_name="tracing",
            protocols=["otlp_http"],
        )

        events = (
            self.on.config_changed,
            self.on.upgrade_charm,
            self.on[CONTAINER_NAME].pebble_ready,
            self.on[STORAGE_NAME].storage_attached,
            self.on[CONTAINER_NAME].pebble_check_failed,
            self.on[CONTAINER_NAME].pebble_check_recovered,
            self.on["ingress"].relation_created,
            self.on["ingress"].relation_joined,
            self.on["ingress"].relation_changed,
            self.on["ingress"].relation_departed,
            self.on["ingress"].relation_broken,
            self._tracing.on.endpoint_changed,
            self._tracing.on.endpoint_removed,
        )
        for event in events:
            framework.observe(event, self._reconcile)
        framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)

    def _tracing_config(self) -> TracingConfig | None:
        """Return valid optional tracing data, ignoring unavailable provider state."""
        if not self._tracing.is_ready():
            return None
        try:
            endpoint = self._tracing.get_endpoint("otlp_http")
        except ProtocolNotRequestedError:
            logger.debug("Tracing protocol request is not visible on this unit yet")
            return None
        if endpoint is None:
            return None
        try:
            return load_tracing_config(endpoint)
        except ValidationError as error:
            logger.warning("%s; tracing disabled", tracing_validation_error_message(error))
            return None

    def _reconcile(self, _: ops.EventBase) -> None:
        """Read, validate, plan, and apply the complete desired state."""
        try:
            config = load_config(self.config)
        except ValidationError as error:
            self.unit.status = ops.BlockedStatus(validation_error_message(error))
            return
        tracing = self._tracing_config()
        if not self.model.storages[STORAGE_NAME]:
            self.unit.status = ops.WaitingStatus("Waiting for persistent storage")
            return

        if not self._workload.can_connect():
            self.unit.status = ops.WaitingStatus("Waiting for Verdaccio container")
            return

        plan = build_plan(
            config,
            service_name=self.app.name,
            ingress_url=self._ingress.url,
            tracing=tracing,
        )
        self.unit.status = ops.MaintenanceStatus("Reconciling Verdaccio")
        self.unit.set_ports(*plan.open_ports)
        self._ingress.provide_ingress_requirements(
            scheme=config.listen_protocol,
            port=config.listen_port,
        )
        try:
            self._workload.apply(plan)
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
        if not self.model.storages[STORAGE_NAME]:
            event.add_status(ops.WaitingStatus("Waiting for persistent storage"))
            return

        if not self._workload.can_connect():
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        try:
            running = self._workload.is_running()
            healthy = running and self._workload.is_healthy()
        except WorkloadUnavailableError:
            event.add_status(ops.WaitingStatus("Waiting for Verdaccio container"))
            return

        if not running:
            event.add_status(ops.MaintenanceStatus("Waiting for Verdaccio service"))
            return

        if not healthy:
            event.add_status(ops.MaintenanceStatus("Waiting for Verdaccio health check"))
            return

        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(VerdaccioK8SCharm)
