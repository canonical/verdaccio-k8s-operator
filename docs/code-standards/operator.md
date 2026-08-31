# Operator Standards

Standards for Python operator and charm development.

> **Scope:** Event-driven operators built with the Ops framework and Pydantic 2.

## cs:operator.configuration.schema_boundary

All untrusted configuration must cross a Pydantic model boundary before business logic or reconciliation uses it, because a single typed boundary prevents validation, defaults, and normalization from being duplicated throughout event handlers.

### Do

Validate the complete configuration snapshot once at the boundary

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OperatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    hostname: str = Field(min_length=1)
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    worker_count: int = Field(default=2, ge=1, le=64)


def load_config(raw: dict[str, object]) -> OperatorConfig:
    return OperatorConfig.model_validate(raw)
```

### Don't

Read and coerce individual values wherever they happen to be needed

```python
def configure(charm) -> None:
    workers = int(charm.config.get("worker-count", 2))  # Bad: ad hoc validation
    debug = charm.config.get("log-level") == "debug"   # Bad: raw config escapes
```

---

## cs:operator.configuration.closed_immutable_models

Configuration and relation models must normally use `ConfigDict(extra="forbid", frozen=True)` so misspelled or obsolete input fails visibly and a validated snapshot cannot change midway through reconciliation; `extra="ignore"` may be used only for a documented, versioned external payload that intentionally permits unknown fields.

### Do

Reject unknown fields and make the validated snapshot immutable

```python
from pydantic import BaseModel, ConfigDict


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint: str
    username: str
    password: str
```

### Don't

Silently discard unknown operator-owned configuration

```python
class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Bad: typos look accepted

    endpoint: str
```

---

## cs:operator.configuration.semantic_types

Models must express domain constraints with semantic types, constrained fields, literals, and model validators rather than accepting broad strings and integers, because type-correct but invalid values otherwise survive until a remote system or workload rejects them.

### Do

Encode field and cross-field invariants in the schema

```python
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class ListenerConfig(BaseModel):
    protocol: Literal["http", "https"]
    port: int = Field(ge=1, le=65535)
    certificate_secret_id: str | None = None

    @model_validator(mode="after")
    def require_certificate_for_https(self) -> Self:
        if self.protocol == "https" and self.certificate_secret_id is None:
            raise ValueError("certificate_secret_id is required for HTTPS")
        return self
```

### Don't

Defer known constraints to scattered conditionals

```python
class ListenerConfig(BaseModel):
    protocol: str  # Bad: accepts unsupported protocols
    port: int      # Bad: accepts invalid TCP ports
```

---

## cs:operator.configuration.source_adapters

Framework objects, relation data bags, environment variables, and secret APIs must be translated by source adapters into plain mappings before model validation; Pydantic models must not reach back into the framework, because separating acquisition from validation keeps models deterministic and testable.

### Do

Acquire raw values in an adapter and validate a plain mapping

```python
from collections.abc import Mapping


def config_input(config: Mapping[str, object]) -> dict[str, object]:
    return {
        "hostname": config["hostname"],
        "log_level": config.get("log-level", "info"),
        "worker_count": config.get("worker-count", 2),
    }


validated = OperatorConfig.model_validate(config_input(charm.config))
```

### Don't

Pass framework objects into model constructors or validators

```python
class OperatorConfig(BaseModel):
    charm: object  # Bad: schema is coupled to live framework state

    @property
    def hostname(self) -> str:
        return self.charm.config["hostname"]
```

---

## cs:operator.configuration.secrets

Secret identifiers must be resolved at the input boundary, represented with `SecretStr` while in memory, and revealed only in the final workload or relation payload; code must not log, interpolate into status messages, or persist secret values in operator state, because those surfaces are routinely exposed to users and diagnostics.

### Do

Keep resolved values redacted until the output boundary

```python
from pydantic import BaseModel, ConfigDict, SecretStr


class Credentials(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str
    password: SecretStr


def workload_environment(credentials: Credentials) -> dict[str, str]:
    return {
        "APP_USERNAME": credentials.username,
        "APP_PASSWORD": credentials.password.get_secret_value(),
    }
```

### Don't

Treat secret references as values or expose resolved content

```python
password = charm.config["password"]
logger.info("Using password %s", password)  # Bad: leaks a secret or secret ID
stored_state.password = password            # Bad: persists sensitive material
```

---

## cs:operator.configuration.output_serialization

Workload and relation output must be produced by an explicit serializer that returns the exact target type, usually `dict[str, str]`; serializers must define aliases and canonical encodings for booleans, enums, URLs, and omitted values, because Python's incidental string representations are not stable external protocols.

### Do

Serialize through a target-specific model method

```python
from pydantic import BaseModel, Field, field_serializer


class WorkloadConfig(BaseModel):
    enabled: bool = Field(serialization_alias="APP_ENABLED")
    timeout_seconds: int = Field(serialization_alias="APP_TIMEOUT_SECONDS")

    @field_serializer("enabled")
    def serialize_enabled(self, value: bool) -> str:
        return "true" if value else "false"

    @field_serializer("timeout_seconds")
    def serialize_timeout(self, value: int) -> str:
        return str(value)

    def as_environment(self) -> dict[str, str]:
        return self.model_dump(by_alias=True)
```

### Don't

Send raw model dumps or arbitrary framework values to a string protocol

```python
environment = dict(charm.config)  # Bad: values may be bool, int, None, or secret IDs
container.add_layer("app", {"services": {"app": {"environment": environment}}})
```

---

## cs:operator.configuration.precedence

When effective configuration combines operator options, relation data, discovered values, and computed defaults, the precedence order must be explicit in one assembly function and covered by behavior tests; code must not rely on the visual order of unrelated dictionary expansions, because a later source can silently override a value owned by another source.

### Do

Name each source and encode precedence deliberately

```python
def effective_config(
    defaults: dict[str, str],
    relation: dict[str, str],
    operator: dict[str, str],
) -> dict[str, str]:
    result = defaults.copy()
    result.update(relation)
    result.update(operator)  # Documented: explicit operator values win.
    return result
```

### Don't

Merge unnamed sources at the point of use

```python
environment = {**computed, **relation_data, **raw_config, **extra}  # Bad: unclear ownership
```

---

## cs:operator.configuration.validation_failure

A `ValidationError` must be converted at the reconciliation boundary into a concise blocked outcome that identifies actionable fields without exposing secret inputs; event handlers must not crash or continue with a partial configuration, because invalid operator input requires user action and cannot produce a trustworthy desired state.

### Do

Stop reconciliation with an actionable blocked result

```python
from pydantic import ValidationError


def reconcile(charm) -> None:
    try:
        config = OperatorConfig.model_validate(config_input(charm.config))
    except ValidationError as error:
        fields = ", ".join(".".join(map(str, item["loc"])) for item in error.errors())
        charm.unit.status = ops.BlockedStatus(f"Invalid configuration: {fields}")
        return

    apply_desired_state(charm, config)
```

### Don't

Catch all errors and proceed with guessed defaults

```python
try:
    config = OperatorConfig.model_validate(raw)
except Exception:
    config = OperatorConfig(hostname="localhost")  # Bad: hides invalid user input
```

---

## cs:operator.events.holistic_reconciliation

State-change events should converge through one holistic reconciler that reads current state and computes the full desired state; dedicated handlers should be reserved for synchronous actions, teardown semantics, and events with genuinely distinct contracts, because delta handlers become order-dependent and leave stale state when events are missed or repeated.

### Do

Route independent state-change events to the same reconciler

```python
class ApplicationCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        events = (
            self.on.config_changed,
            self.on.app_pebble_ready,
            self.on["database"].relation_changed,
            self.on["database"].relation_broken,
            self.on.secret_changed,
        )
        for event in events:
            framework.observe(event, self._reconcile)

    def _reconcile(self, _: ops.EventBase) -> None:
        snapshot = self._read_current_state()
        desired = build_desired_state(snapshot)
        self._apply(desired)
```

### Don't

Let each event mutate only its perceived delta

```python
def _on_database_changed(self, event) -> None:
    self._write_database_config(event.relation.data)  # Bad: preserves unrelated stale state


def _on_config_changed(self, event) -> None:
    self._write_user_config()  # Bad: final state depends on event order
```

---

## cs:operator.events.current_state

Reconciliation must derive decisions from current model, relation, secret, container, and persisted state rather than treating an event payload as the source of truth, because deferred delivery, coalesced events, leadership changes, and relation departure can make the triggering payload stale by the time a handler runs.

### Do

Use the event as a trigger and re-read authoritative state

```python
def _reconcile(self, _: ops.EventBase) -> None:
    relation = self.model.get_relation("database")
    database = read_database_relation(relation) if relation else None
    desired = build_desired_state(config=self.config, database=database)
    self._apply(desired)
```

### Don't

Replay an event payload as though it were durable state

```python
def _on_relation_changed(self, event) -> None:
    self._apply_database(event.relation.data[event.app])  # Bad: payload may already be stale
```

---

## cs:operator.events.reconcile_phases

A reconciler should have explicit read, validate, plan, and apply phases, and desired-state construction should be pure; code must not interleave remote reads and mutations while still deciding the plan, because partial failure then leaves the unit in an unrepeatable intermediate state.

### Do

Build a complete plan before applying side effects

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    environment: dict[str, str]
    relation_payload: dict[str, str] | None
    open_ports: frozenset[int]


def _reconcile(self, _: ops.EventBase) -> None:
    snapshot = self._read_current_state()
    validated = validate_snapshot(snapshot)
    plan = build_plan(validated)
    self._apply_plan(plan)
```

### Don't

Mutate the system while gathering prerequisites

```python
def _reconcile(self, event) -> None:
    self.unit.open_port("tcp", 8080)
    credentials = self._read_database()  # Bad: later failure leaves a partial change
    self.container.replan()
```

---

## cs:operator.events.prerequisite_outcomes

Missing prerequisites must produce explicit reconciliation outcomes: `blocked` for conditions requiring user intervention, `waiting` for expected external progress, and a normal no-op for optional capabilities; a missing prerequisite must not be represented as an exception or an implicit empty mapping, because those forms erase whether reconciliation may safely continue.

### Do

Classify readiness before constructing desired state

```python
def readiness(snapshot: Snapshot) -> ops.StatusBase | None:
    if snapshot.config_error:
        return ops.BlockedStatus("Invalid configuration: hostname")
    if snapshot.database_required and snapshot.database is None:
        return ops.WaitingStatus("Waiting for database relation data")
    return None


def _reconcile(self, _: ops.EventBase) -> None:
    snapshot = self._read_current_state()
    if status := readiness(snapshot):
        self.unit.status = status
        return
    self._apply_plan(build_plan(snapshot))
```

### Don't

Collapse not-ready, optional, and invalid states into an empty value

```python
database = fetch_database_data() or {}  # Bad: absence has no defined meaning
self._apply_environment(database)
```

---

## cs:operator.events.defer_sparingly

Handlers should rely on future state-change events and return when a prerequisite is absent; `event.defer()` may be used only for a transient condition expected to clear without a reliable future event, and a deferring handler must return immediately and be safe to restart from the beginning, because deferred handler executions can accumulate and run against newer state.

### Do

Return for event-driven readiness and defer only a retryable failure without another trigger

```python
def _on_relation_changed(self, event: ops.RelationChangedEvent) -> None:
    if not relation_is_ready(event.relation):
        return  # A later relation-changed event will retry reconciliation.
    self._reconcile(event)


def _on_storage_attached(self, event: ops.StorageAttachedEvent) -> None:
    try:
        prepare_storage()
    except TemporaryStorageError:
        event.defer()
        return
```

### Don't

Defer every event that observes an unmet dependency

```python
def _reconcile(self, event: ops.EventBase) -> None:
    if not self.container.can_connect():
        event.defer()  # Bad: pebble-ready already provides the next trigger
        return
```

---

## cs:operator.events.idempotent_effects

Every reconciliation effect must be idempotent and change-aware: compare current and desired content before writing, publish deterministic relation data, synchronize sets such as ports, and restart a workload only when an input that requires restart changed; repeated reconciliation of an already converged unit must cause no externally visible mutation.

### Do

Apply only the difference between current and desired state

```python
def sync_file(container: ops.Container, path: str, desired: str) -> bool:
    current = container.pull(path).read() if container.exists(path) else None
    if current == desired:
        return False
    container.push(path, desired, make_dirs=True)
    return True


changed = sync_file(container, "/etc/app/config.yaml", rendered_config)
if changed:
    container.restart("app")
```

### Don't

Rewrite and restart on every event

```python
container.push("/etc/app/config.yaml", rendered_config)
container.restart("app")  # Bad: repeated events cause unnecessary disruption
```

---

## cs:operator.events.content_changes

When a workload consumes a stable path whose content may rotate, the reconciliation plan must include the content digest or explicitly restart after a changed write; comparing only paths or service definitions is insufficient, because certificate, credential, and configuration rotation can otherwise leave the running process on stale in-memory data.

### Do

Make content changes visible to the service plan

```python
from hashlib import sha256


certificate_digest = sha256(certificate_pem.encode()).hexdigest()
environment = {
    "APP_CERTIFICATE_PATH": "/etc/app/tls/certificate.pem",
    "APP_CERTIFICATE_DIGEST": certificate_digest,
}
container.add_layer("app", service_layer(environment), combine=True)
container.replan()
```

### Don't

Assume an unchanged path means unchanged runtime state

```python
container.push("/etc/app/tls/certificate.pem", rotated_certificate)
container.replan()  # Bad: the service plan is unchanged and may not restart
```

---

## cs:operator.events.relation_contracts

Relation data must be parsed into a typed, version-aware boundary model before it reaches planning logic, and incomplete mandatory payloads must remain not ready rather than being partially applied; relation writers must publish complete deterministic payloads, because data bags are asynchronous string maps rather than transactional typed APIs.

### Do

Validate the relation payload as one contract

```python
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class DatabaseRelation(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    endpoints: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: SecretStr


def read_database(data: dict[str, str]) -> DatabaseRelation | None:
    try:
        return DatabaseRelation.model_validate(data)
    except ValidationError:
        return None
```

### Don't

Apply whichever relation keys happen to be present

```python
if "endpoints" in data:
    environment["DB_HOST"] = data["endpoints"]  # Bad: credentials may still be absent
```

---

## cs:operator.events.leadership

Application-scoped relation writes and singleton operations must be guarded by current leadership at the point of mutation, while unit-scoped workload reconciliation should remain available on every unit; cached leadership must not be persisted, because leadership can change between events and during retries.

### Do

Check leadership immediately before an application-scoped write

```python
def publish_application_data(self, relation: ops.Relation, payload: dict[str, str]) -> None:
    if not self.unit.is_leader():
        return
    relation.data[self.app].update(payload)
```

### Don't

Cache leadership or skip all reconciliation on non-leaders

```python
self._is_leader = self.unit.is_leader()


def _reconcile(self, event) -> None:
    if not self._is_leader:  # Bad: stale and prevents unit-scoped convergence
        return
```

---

## cs:operator.events.status_collection

Status collection must be side-effect free and derive status from current validated state, relation readiness, and workload health using a deterministic priority; reconcilers may record facts needed for status but must not rely on a stale status value as control flow, because status events can run independently after any hook.

### Do

Collect status from current facts without mutating managed resources

```python
def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
    snapshot = self._read_current_state()
    if snapshot.config_error:
        event.add_status(ops.BlockedStatus("Invalid configuration"))
    elif not snapshot.dependencies_ready:
        event.add_status(ops.WaitingStatus("Waiting for dependencies"))
    elif not snapshot.service_ready:
        event.add_status(ops.MaintenanceStatus("Waiting for service"))
    else:
        event.add_status(ops.ActiveStatus())
```

### Don't

Configure resources or use status as persisted application state

```python
def _on_collect_status(self, event) -> None:
    self.container.replan()  # Bad: status collection has side effects
    if isinstance(self.unit.status, ops.ActiveStatus):
        event.add_status(self.unit.status)  # Bad: repeats stale status
```

---

## cs:operator.events.persisted_state

Persisted state must contain only irreducible historical facts such as a completed one-time migration or an acknowledged generation; configuration, leadership, relation data, readiness, and renderable desired state must be recomputed from authoritative sources, because copied state becomes stale and creates a second source of truth.

### Do

Persist only history that cannot be reconstructed

```python
from ops.framework import StoredState


class ApplicationCharm(ops.CharmBase):
    _stored = StoredState()

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        self._stored.set_default(completed_migrations=[])
```

### Don't

Mirror current framework state into storage

```python
self._stored.config = dict(self.config)          # Bad: duplicates authoritative config
self._stored.database = relation.data[relation.app]  # Bad: relation data can change
self._stored.is_leader = self.unit.is_leader()   # Bad: leadership is transient
```

---

## cs:operator.events.action_boundaries

Actions must use dedicated synchronous handlers that validate parameters, check readiness, perform one bounded operation, and call `event.fail()` with an actionable message on expected failure; actions must not be deferred or routed through a reconciler that can silently return, because callers require a definitive result from the current invocation.

### Do

Validate and terminate the action explicitly

```python
def _on_rotate_token(self, event: ops.ActionEvent) -> None:
    try:
        params = RotateTokenParams.model_validate(event.params)
        token = rotate_token(params.username)
    except ValidationError as error:
        event.fail(f"Invalid parameters: {error.errors()[0]['msg']}")
        return
    except WorkloadUnavailable:
        event.fail("Workload is not ready")
        return
    event.set_results({"token": token})
```

### Don't

Defer an action or report success after a partial failure

```python
def _on_rotate_token(self, event: ops.ActionEvent) -> None:
    if not self.container.can_connect():
        event.defer()  # Bad: actions are synchronous and cannot be deferred
        return
    self._reconcile(event)  # Bad: no action-specific result contract
```

---

## cs:operator.execution.argv_commands

Workload commands must be passed as argument vectors whenever the API supports them, and shell execution may be used only when shell semantics are required with every untrusted token quoted; string concatenation must not construct commands from config, relation, or action values, because validation does not prevent shell interpretation.

### Do

Pass each argument directly to the workload process

```python
process = container.exec(
    [
        "/usr/bin/appctl",
        "create-user",
        "--username",
        params.username,
        "--role",
        params.role,
    ]
)
stdout, _ = process.wait_output()
```

### Don't

Interpolate user-controlled values into a shell command

```python
command = f"appctl create-user --username {event.params['username']}"
container.exec(["/bin/sh", "-c", command])  # Bad: shell injection boundary
```

---

## cs:operator.testing.event_transitions

Tests must exercise observable state transitions through the Ops testing context, including events arriving in different orders, missing and restored prerequisites, relation removal, secret rotation, leadership changes, and invalid configuration; tests should assert resulting plans, relation data, opened ports, statuses, and action results rather than private helper calls, because event-driven correctness is a property of transitions rather than isolated functions.

### Do

Test the same reconciler from multiple triggering events

```python
import pytest
from ops import testing


@pytest.mark.parametrize("trigger", ["config_changed", "pebble_ready", "relation_changed"])
def test_ready_inputs_converge_to_the_same_plan(trigger: str) -> None:
    context = testing.Context(ApplicationCharm)
    state = ready_state()

    output = context.run(event_for(context, trigger, state), state)

    assert output.get_container("app").plan == expected_plan()
    assert output.unit_status == testing.ActiveStatus()
```

### Don't

Prove only that a private helper returns a mocked value

```python
def test_reconcile_calls_render(mocker):
    charm = mocker.Mock()
    charm._render.return_value = "config"
    charm._reconcile(mocker.Mock())
    charm._render.assert_called_once()  # Bad: no state transition is verified
```

---

## cs:operator.testing.convergence

At least one test for every reconciled resource must run reconciliation twice from the first output state and assert that the second run causes no additional mutation or disruption; restart, write, and publication counters may be inspected when supported, because a correct final snapshot alone can hide non-idempotent behavior.

### Do

Verify a converged state remains unchanged

```python
def test_reconcile_is_idempotent() -> None:
    context = testing.Context(ApplicationCharm)
    initial = ready_state()

    first = context.run(context.on.config_changed(), initial)
    second = context.run(context.on.config_changed(), first)

    assert second == first
    assert service_restart_count(second) == service_restart_count(first)
```

### Don't

Stop after the first successful convergence

```python
def test_config_changed_starts_service() -> None:
    output = context.run(context.on.config_changed(), ready_state())
    assert output.get_container("app").service_statuses["app"].name == "ACTIVE"
    # Bad: repeated reconciliation behavior is untested.
```
