#!/usr/bin/env python3
"""Orchestrate Verdaccio reconciliation events and status."""

import json
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

from config import (
    CharmConfig,
    TracingConfig,
    load_tracing_config,
    tracing_validation_error_message,
    validation_error_message,
)
from management import (
    MANAGE_USER_PARAMS_ADAPTER,
    ManagementError,
    ManagementUnavailableError,
    ManageTokenParams,
    VerdaccioManagement,
    action_validation_error,
    htpasswd_settings,
    token_database_path,
    token_status,
)
from secret_config import SecretConfigurationError, load_secret_backed_config
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
SCALING_BLOCK_MESSAGE = "Scale down to one unit; local storage cannot be shared"


class VerdaccioK8SCharm(ops.CharmBase):
    """Operate a single Verdaccio workload container."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        container = self.unit.get_container(CONTAINER_NAME)
        self._workload = VerdaccioWorkload(container)
        self._management = VerdaccioManagement(container)
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
            self.on.update_status,
            self.on.secret_changed,
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
        framework.observe(self.on["manage-user"].action, self._on_manage_user_action)
        framework.observe(self.on["manage-token"].action, self._on_manage_token_action)

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

    def _management_config(self, event: ops.ActionEvent) -> CharmConfig | None:
        """Validate and return the current configuration snapshot."""
        try:
            return load_secret_backed_config(self.model, self.config)
        except SecretConfigurationError as error:
            event.fail(error.status_message)
        except ValidationError as error:
            event.fail(validation_error_message(error))
        return None

    def _require_management_target(self, event: ops.ActionEvent) -> bool:
        """Require the single running workload needed by stateful actions."""
        if self.app.planned_units() > 1:
            event.fail(SCALING_BLOCK_MESSAGE)
            return False
        if not self.model.storages[STORAGE_NAME]:
            event.fail("Persistent storage is not attached")
            return False
        if not self._management.can_connect():
            event.fail("Verdaccio container is not ready")
            return False
        try:
            if not self._management.is_running():
                event.fail("Verdaccio service is not running")
                return False
        except ManagementUnavailableError as error:
            event.fail(str(error))
            return False
        return True

    def _on_manage_user_action(self, event: ops.ActionEvent) -> None:
        """Create, reset, remove, or list users in the configured htpasswd backend."""
        try:
            params = MANAGE_USER_PARAMS_ADAPTER.validate_python(event.params)
        except ValidationError as error:
            event.fail(action_validation_error(error))
            return
        config = self._management_config(event)
        if config is None:
            return
        if not self._require_management_target(event):
            return
        try:
            path, algorithm, rounds, validation = htpasswd_settings(config)
            result = self._management.manage_user(
                params.operation,
                path,
                username=params.username,
                algorithm=algorithm,
                rounds=rounds,
                validation=validation,
            )
        except ManagementError as error:
            event.fail(str(error))
            return
        except ManagementUnavailableError as error:
            event.fail(str(error))
            return

        if params.operation == "list":
            users = result.get("users")
            if not isinstance(users, list) or not all(isinstance(user, str) for user in users):
                event.fail("Management helper returned an invalid user list")
                return
            event.set_results({"users": json.dumps(users), "count": str(len(users))})
            return

        action_result: dict[str, str] = {"username": params.username}
        password = result.get("password")
        if isinstance(password, str):
            action_result["password"] = password
        event.set_results(action_result)

    def _on_manage_token_action(self, event: ops.ActionEvent) -> None:
        """Report token settings or invalidate every issued token."""
        try:
            params = ManageTokenParams.model_validate(event.params)
        except ValidationError as error:
            event.fail(action_validation_error(error))
            return
        config = self._management_config(event)
        if config is None:
            return
        results = token_status(config)
        if params.operation == "revoke-all":
            if not self._require_management_target(event):
                return
            try:
                self._management.revoke_all_tokens(token_database_path(config))
            except ManagementError as error:
                event.fail(str(error))
                return
            except ManagementUnavailableError as error:
                event.fail(str(error))
                return
            results["revoked"] = "all"
        event.set_results(results)

    def _reconcile(self, _: ops.EventBase) -> None:
        """Read, validate, plan, and apply the complete desired state."""
        if self.app.planned_units() > 1:
            self.unit.status = ops.BlockedStatus(SCALING_BLOCK_MESSAGE)
            return
        try:
            config = load_secret_backed_config(self.model, self.config)
        except SecretConfigurationError as error:
            self.unit.status = ops.BlockedStatus(error.status_message)
            return
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
            return

        try:
            workload_version = self._workload.version()
        except WorkloadUnavailableError as error:
            logger.warning("Could not read the Verdaccio version: %s", error)
        else:
            if workload_version is not None:
                self.unit.set_workload_version(workload_version)

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent) -> None:
        """Report status from current validated inputs and workload health."""
        if self.app.planned_units() > 1:
            event.add_status(ops.BlockedStatus(SCALING_BLOCK_MESSAGE))
            return
        try:
            load_secret_backed_config(self.model, self.config, refresh=False)
        except SecretConfigurationError as error:
            event.add_status(ops.BlockedStatus(error.status_message))
            return
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
