import json
from dataclasses import replace
from typing import cast

import pytest
from helpers import verdaccio_container
from ops import pebble, testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from management import (
    MANAGEMENT_PATH,
    NODE_PATH,
    SHUTDOWN_CHECK_COMMAND,
    ManagementUnavailableError,
    VerdaccioManagement,
)
from workload import SERVICE_NAME

HTPASSWD_PATH = "/verdaccio/storage/htpasswd"
TOKEN_DATABASE_PATH = "/verdaccio/storage/.verdaccio-db.json"


def _ready_state(
    *,
    execs: tuple[testing.Exec, ...] = (),
    config: dict[str, str | int | float | bool] | None = None,
    can_connect: bool = True,
    service_status: pebble.ServiceStatus = pebble.ServiceStatus.ACTIVE,
    storage_attached: bool = True,
    planned_units: int = 1,
) -> tuple[testing.Context[VerdaccioK8SCharm], testing.State]:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(
        can_connect=True,
        execs=(testing.Exec(list(SHUTDOWN_CHECK_COMMAND)), *execs),
    )
    storage = testing.Storage(STORAGE_NAME)
    state = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(
            config=config or {},
            containers={container},
            storages={storage},
        ),
    )
    ready_container = state.get_container("verdaccio")
    action_container = replace(
        ready_container,
        can_connect=can_connect,
        service_statuses={SERVICE_NAME: service_status},
    )
    state = replace(
        state,
        containers={action_container},
        storages={storage} if storage_attached else set(),
        planned_units=planned_units,
    )
    return ctx, state


@pytest.mark.parametrize("operation", ["create", "reset-password"])
def test_manage_user_returns_generated_password(operation: str) -> None:
    password = "Generated-Password-123!"
    command = [
        NODE_PATH,
        MANAGEMENT_PATH,
        "user",
        operation,
        HTPASSWD_PATH,
        "admin",
        "bcrypt",
        "10",
        ".{3}$",
    ]
    ctx, state = _ready_state(
        execs=(
            testing.Exec(
                command,
                stdout=json.dumps({"username": "admin", "password": password}),
            ),
        )
    )

    output = ctx.run(
        ctx.on.action("manage-user", params={"operation": operation, "username": "admin"}),
        state,
    )

    assert ctx.action_results == {"username": "admin", "password": password}
    assert (
        output.get_container("verdaccio").service_statuses[SERVICE_NAME]
        is pebble.ServiceStatus.ACTIVE
    )


def test_manage_user_lists_admin_and_other_users() -> None:
    command = [NODE_PATH, MANAGEMENT_PATH, "user", "list", HTPASSWD_PATH]
    ctx, state = _ready_state(
        execs=(
            testing.Exec(
                command,
                stdout=json.dumps({"users": ["admin", "alice"]}),
            ),
        )
    )

    ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)

    assert ctx.action_results == {"users": '["admin", "alice"]', "count": "2"}


def test_manage_user_rejects_username_for_list() -> None:
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="username"):
        ctx.run(
            ctx.on.action("manage-user", params={"operation": "list", "username": "admin"}),
            state,
        )


def test_manage_user_rejects_invalid_helper_user_list() -> None:
    command = [NODE_PATH, MANAGEMENT_PATH, "user", "list", HTPASSWD_PATH]
    ctx, state = _ready_state(
        execs=(testing.Exec(command, stdout=json.dumps({"users": "admin"})),)
    )

    with pytest.raises(testing.ActionFailed, match="invalid user list"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_removes_user_and_restores_service() -> None:
    command = [
        NODE_PATH,
        MANAGEMENT_PATH,
        "user",
        "remove",
        HTPASSWD_PATH,
        "alice",
        "bcrypt",
        "10",
        ".{3}$",
    ]
    ctx, state = _ready_state(
        execs=(testing.Exec(command, stdout=json.dumps({"username": "alice"})),)
    )

    output = ctx.run(
        ctx.on.action("manage-user", params={"operation": "remove", "username": "alice"}),
        state,
    )

    assert ctx.action_results == {"username": "alice"}
    assert (
        output.get_container("verdaccio").service_statuses[SERVICE_NAME]
        is pebble.ServiceStatus.ACTIVE
    )


def test_manage_user_rejects_missing_username() -> None:
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="username.*Field required"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "create"}), state)


def test_manage_user_reports_workload_rejection() -> None:
    command = [
        NODE_PATH,
        MANAGEMENT_PATH,
        "user",
        "create",
        HTPASSWD_PATH,
        "alice",
        "bcrypt",
        "10",
        ".{3}$",
    ]
    ctx, state = _ready_state(
        execs=(testing.Exec(command, return_code=1, stderr="User 'alice' already exists\n"),)
    )

    with pytest.raises(testing.ActionFailed, match="already exists"):
        ctx.run(
            ctx.on.action("manage-user", params={"operation": "create", "username": "alice"}),
            state,
        )


def test_manage_user_rejects_non_htpasswd_authentication() -> None:
    ctx, state = _ready_state(config={"auth-config": "company-auth: {endpoint: ldap}"})

    with pytest.raises(testing.ActionFailed, match="requires htpasswd as the only auth plugin"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_rejects_multiple_planned_units() -> None:
    ctx, state = _ready_state(planned_units=2)

    with pytest.raises(testing.ActionFailed, match="Scale down to one unit"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_rejects_detached_storage() -> None:
    ctx, state = _ready_state(storage_attached=False)

    with pytest.raises(testing.ActionFailed, match="Persistent storage is not attached"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_rejects_disconnected_container() -> None:
    ctx, state = _ready_state(can_connect=False)

    with pytest.raises(testing.ActionFailed, match="Verdaccio container is not ready"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_rejects_stopped_service() -> None:
    ctx, state = _ready_state(service_status=pebble.ServiceStatus.INACTIVE)

    with pytest.raises(testing.ActionFailed, match="Verdaccio service is not running"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_manage_user_reports_service_inspection_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(_: VerdaccioManagement) -> bool:
        raise ManagementUnavailableError("Pebble service inspection failed")

    monkeypatch.setattr(VerdaccioManagement, "is_running", unavailable)
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="Pebble service inspection failed"):
        ctx.run(ctx.on.action("manage-user", params={"operation": "list"}), state)


def test_shutdown_wait_failure_restores_service(monkeypatch: pytest.MonkeyPatch) -> None:
    moments = iter((0.0, 0.0, 11.0))
    monkeypatch.setattr("management.time.monotonic", lambda: next(moments))
    monkeypatch.setattr("management.time.sleep", lambda _: None)
    ctx, state = _ready_state(execs=(testing.Exec(list(SHUTDOWN_CHECK_COMMAND), return_code=1),))

    with pytest.raises(testing.ActionFailed, match="did not finish shutting down") as failure:
        ctx.run(
            ctx.on.action("manage-user", params={"operation": "create", "username": "admin"}),
            state,
        )

    assert failure.value.state is not None
    failed_state = cast(testing.State, failure.value.state)
    container = failed_state.get_container("verdaccio")
    assert container.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE


def test_manage_user_preserves_restart_failure_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_restart(_: VerdaccioManagement) -> None:
        raise ManagementUnavailableError(
            "Management operation completed but Verdaccio could not restart"
        )

    monkeypatch.setattr(VerdaccioManagement, "_restore", fail_restart)
    command = [
        NODE_PATH,
        MANAGEMENT_PATH,
        "user",
        "create",
        HTPASSWD_PATH,
        "admin",
        "bcrypt",
        "10",
        ".{3}$",
    ]
    ctx, state = _ready_state(
        execs=(testing.Exec(command, stdout=json.dumps({"username": "admin"})),)
    )

    with pytest.raises(testing.ActionFailed, match="completed but Verdaccio could not restart"):
        ctx.run(
            ctx.on.action("manage-user", params={"operation": "create", "username": "admin"}),
            state,
        )


def test_manage_token_reports_default_modes() -> None:
    ctx, state = _ready_state()

    ctx.run(ctx.on.action("manage-token", params={"operation": "status"}), state)

    assert ctx.action_results == {
        "api-token-mode": "legacy",
        "api-token-expiration": "never",
        "web-token-mode": "jwt",
        "web-token-expiration": "1h",
    }


def test_manage_token_status_does_not_require_workload_readiness() -> None:
    ctx, state = _ready_state(
        can_connect=False,
        service_status=pebble.ServiceStatus.INACTIVE,
        storage_attached=False,
        planned_units=2,
    )

    ctx.run(ctx.on.action("manage-token", params={"operation": "status"}), state)

    assert ctx.action_results is not None
    assert ctx.action_results["api-token-mode"] == "legacy"


def test_manage_token_status_rejects_confirmation() -> None:
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="confirm is not accepted for status"):
        ctx.run(
            ctx.on.action("manage-token", params={"operation": "status", "confirm": True}),
            state,
        )


def test_manage_token_reports_explicitly_disabled_legacy_mode_as_jwt() -> None:
    ctx, state = _ready_state(config={"security-config": "api: {legacy: false}"})

    ctx.run(ctx.on.action("manage-token", params={"operation": "status"}), state)

    assert ctx.action_results is not None
    assert ctx.action_results["api-token-mode"] == "jwt"
    assert ctx.action_results["api-token-expiration"] == "verdaccio-default"


def test_manage_token_revokes_all_tokens_and_restores_service() -> None:
    command = [NODE_PATH, MANAGEMENT_PATH, "token", "revoke-all", TOKEN_DATABASE_PATH]
    ctx, state = _ready_state(
        execs=(testing.Exec(command, stdout=json.dumps({"revoked": "all"})),)
    )

    output = ctx.run(
        ctx.on.action(
            "manage-token",
            params={"operation": "revoke-all", "confirm": True},
        ),
        state,
    )

    assert ctx.action_results is not None
    assert ctx.action_results["revoked"] == "all"
    assert (
        output.get_container("verdaccio").service_statuses[SERVICE_NAME]
        is pebble.ServiceStatus.ACTIVE
    )


def test_manage_token_preserves_management_failure_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_revocation(_: VerdaccioManagement, __: str) -> None:
        raise ManagementUnavailableError(
            "Management operation completed but Verdaccio could not restart"
        )

    monkeypatch.setattr(VerdaccioManagement, "revoke_all_tokens", fail_revocation)
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="completed but Verdaccio could not restart"):
        ctx.run(
            ctx.on.action(
                "manage-token",
                params={"operation": "revoke-all", "confirm": True},
            ),
            state,
        )


def test_manage_token_requires_global_revocation_confirmation() -> None:
    ctx, state = _ready_state()

    with pytest.raises(testing.ActionFailed, match="confirm=true is required"):
        ctx.run(ctx.on.action("manage-token", params={"operation": "revoke-all"}), state)


def test_manage_token_rejects_global_revocation_for_custom_storage() -> None:
    ctx, state = _ready_state(config={"storage-path": "", "store-config": "memory: {limit: 1000}"})

    with pytest.raises(testing.ActionFailed, match="requires Verdaccio local storage"):
        ctx.run(
            ctx.on.action(
                "manage-token",
                params={"operation": "revoke-all", "confirm": True},
            ),
            state,
        )
