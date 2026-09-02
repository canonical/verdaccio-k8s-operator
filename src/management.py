"""Validate management action parameters and resolve their workload targets."""

import json
import time
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

import ops
from pydantic import Field, TypeAdapter, ValidationError, model_validator

from config import CharmConfig, ConfigModel, HtpasswdConfig
from workload import CONFIG_PATH, METRICS_PORT, SERVICE_NAME, WORKING_DIRECTORY, WORKLOAD_USER_ID

DEFAULT_PASSWORD_VALIDATION = ".{3}$"
MANAGEMENT_PATH = "/opt/verdaccio-app/management.mjs"
NODE_PATH = "/bin/node"
TOKEN_DATABASE_NAME = ".verdaccio-db.json"
SHUTDOWN_CHECK_COMMAND = (
    NODE_PATH,
    "-e",
    (
        'const server = require("node:net").createServer();'
        'server.once("error", () => process.exit(1));'
        f'server.listen({{host: "0.0.0.0", port: {METRICS_PORT}}}, '
        "() => server.close(() => process.exit(0)));"
    ),
)


class ManagementError(Exception):
    """A requested management operation is unsupported by the current configuration."""


class ManagementUnavailableError(Exception):
    """The workload container cannot currently satisfy a management operation."""


class ManageUserListParams(ConfigModel):
    """Parameters for listing htpasswd users."""

    operation: Literal["list"]
    username: None = None


class ManageUserMutationParams(ConfigModel):
    """Parameters for one htpasswd user mutation."""

    operation: Literal["create", "reset-password", "remove"]
    username: str = Field(min_length=1)


ManageUserParams = Annotated[
    ManageUserListParams | ManageUserMutationParams,
    Field(discriminator="operation"),
]
MANAGE_USER_PARAMS_ADAPTER = TypeAdapter(ManageUserParams)


class ManageTokenParams(ConfigModel):
    """Parameters for token inspection or global revocation."""

    operation: Literal["status", "revoke-all"]
    confirm: bool = False

    @model_validator(mode="after")
    def require_revocation_confirmation(self) -> Self:
        """Make global token revocation explicit while keeping status read-only."""
        if self.operation == "revoke-all" and not self.confirm:
            raise ValueError("confirm=true is required for revoke-all")
        if self.operation == "status" and self.confirm:
            raise ValueError("confirm is not accepted for status")
        return self


def action_validation_error(error: ValidationError) -> str:
    """Return one concise action parameter error without echoing input values."""
    item = error.errors(include_input=False)[0]
    message = str(item["msg"]).removeprefix("Value error, ")
    location = ".".join(str(part) for part in item["loc"])
    return (
        f"Invalid parameters: {location}: {message}"
        if location
        else f"Invalid parameters: {message}"
    )


def htpasswd_settings(config: CharmConfig) -> tuple[str, str, int, str]:
    """Return the sole supported htpasswd backend's path and hashing policy."""
    auth = config.verdaccio.auth
    if auth is None or set(auth) != {"htpasswd"}:
        raise ManagementError("User management requires htpasswd as the only auth plugin")
    try:
        htpasswd = HtpasswdConfig.model_validate(auth["htpasswd"])
    except ValidationError as error:
        raise ManagementError("The htpasswd configuration is invalid") from error

    path = PurePosixPath(htpasswd.file)
    if not path.is_absolute():
        path = PurePosixPath(CONFIG_PATH).parent / path
    algorithm = htpasswd.algorithm or "bcrypt"
    rounds = htpasswd.rounds or 10
    server = config.verdaccio.server
    validation = (
        server.password_validation_regex
        if server is not None and server.password_validation_regex is not None
        else DEFAULT_PASSWORD_VALIDATION
    )
    return str(path), algorithm, rounds, validation


def token_database_path(config: CharmConfig) -> str:
    """Return the local storage database that owns Verdaccio's signing secret."""
    verdaccio = config.verdaccio
    if verdaccio.store is not None or verdaccio.storage is None:
        raise ManagementError("Token revocation requires Verdaccio local storage")
    return str(PurePosixPath(verdaccio.storage) / TOKEN_DATABASE_NAME)


def token_status(config: CharmConfig) -> dict[str, str]:
    """Describe the configured API and web token modes without exposing the signing secret."""
    security = config.verdaccio.security
    api = security.api if security is not None else None
    api_jwt = api.jwt if api is not None else None
    web_jwt = security.web if security is not None else None

    if api_jwt is not None or (api is not None and api.legacy is False):
        api_mode = "jwt"
        expires_in = api_jwt.sign.get("expiresIn") if api_jwt is not None else None
        api_expiration = str(expires_in) if expires_in is not None else "verdaccio-default"
    else:
        api_mode = "legacy"
        api_expiration = "never"

    web_expires_in = web_jwt.sign.get("expiresIn") if web_jwt is not None else None
    return {
        "api-token-mode": api_mode,
        "api-token-expiration": api_expiration,
        "web-token-mode": "jwt",
        "web-token-expiration": str(web_expires_in) if web_expires_in is not None else "1h",
    }


class VerdaccioManagement:
    """Execute synchronous user and token operations through Pebble."""

    def __init__(self, container: ops.Container) -> None:
        self._container = container

    def can_connect(self) -> bool:
        """Return whether Pebble is currently reachable."""
        return self._container.can_connect()

    def is_running(self) -> bool:
        """Return whether Verdaccio can accept a management operation."""
        try:
            return self._container.get_service(SERVICE_NAME).is_running()
        except (ops.ModelError, ops.pebble.APIError, ops.pebble.ConnectionError) as error:
            raise ManagementUnavailableError(str(error)) from error

    def manage_user(
        self,
        operation: str,
        path: str,
        *,
        username: str | None = None,
        algorithm: str = "bcrypt",
        rounds: int = 10,
        validation: str = ".{3}$",
    ) -> dict[str, object]:
        """Run one htpasswd user operation and return its structured result."""
        command = [NODE_PATH, MANAGEMENT_PATH, "user", operation, path]
        if username is not None:
            command.extend([username, algorithm, str(rounds), validation])
        return self._run(command, restart=operation != "list")

    def revoke_all_tokens(self, database_path: str) -> None:
        """Rotate the local-storage token secret and restart Verdaccio."""
        self._run(
            [NODE_PATH, MANAGEMENT_PATH, "token", "revoke-all", database_path],
            restart=True,
        )

    def _run(self, command: list[str], *, restart: bool) -> dict[str, object]:
        """Execute a bounded helper operation, restoring the running service afterward."""
        self._prepare()
        if restart:
            try:
                self._stop()
                self._wait_for_shutdown()
                stdout = self._execute(command)
            finally:
                self._restore()
        else:
            stdout = self._execute(command)

        try:
            result = json.loads(stdout)
        except (json.JSONDecodeError, TypeError) as error:
            raise ManagementUnavailableError(
                "Management helper returned an invalid result"
            ) from error
        if not isinstance(result, dict):
            raise ManagementUnavailableError("Management helper returned an invalid result")
        return result

    def _prepare(self) -> None:
        """Require a running service before a management operation."""
        try:
            service = self._container.get_service(SERVICE_NAME)
            if not service.is_running():
                raise ManagementError("Verdaccio service is not running")
        except ManagementError:
            raise
        except (
            ops.ModelError,
            ops.pebble.APIError,
            ops.pebble.ConnectionError,
        ) as error:
            raise ManagementUnavailableError(str(error)) from error

    def _stop(self) -> None:
        """Stop Verdaccio before mutating its persistent state."""
        try:
            self._container.stop(SERVICE_NAME)
        except (
            ops.ModelError,
            ops.pebble.APIError,
            ops.pebble.ChangeError,
            ops.pebble.ConnectionError,
            ops.pebble.TimeoutError,
        ) as error:
            raise ManagementUnavailableError(str(error)) from error

    def _wait_for_shutdown(self) -> None:
        """Wait until the old telemetry listener releases its port."""
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                process = self._container.exec(list(SHUTDOWN_CHECK_COMMAND), timeout=2)
                process.wait()
                return
            except ops.pebble.ExecError:
                pass
            except (
                ops.ModelError,
                ops.pebble.APIError,
                ops.pebble.ChangeError,
                ops.pebble.ConnectionError,
                ops.pebble.TimeoutError,
            ) as error:
                raise ManagementUnavailableError(str(error)) from error
            time.sleep(0.1)
        raise ManagementUnavailableError("Verdaccio did not finish shutting down")

    def _execute(self, command: list[str]) -> str:
        """Execute the management helper and classify expected workload rejection."""
        try:
            process = self._container.exec(
                command,
                timeout=60,
                user_id=WORKLOAD_USER_ID,
                working_dir=WORKING_DIRECTORY,
            )
            stdout, _ = process.wait_output()
            return stdout
        except ops.pebble.ExecError as error:
            detail = (error.stderr or "").strip() or "Management operation failed"
            raise ManagementError(detail) from error
        except (
            ops.ModelError,
            ops.pebble.APIError,
            ops.pebble.ChangeError,
            ops.pebble.ConnectionError,
            ops.pebble.TimeoutError,
        ) as error:
            raise ManagementUnavailableError(str(error)) from error

    def _restore(self) -> None:
        """Restart Verdaccio after a mutating management operation."""
        try:
            self._container.start(SERVICE_NAME)
        except (
            ops.ModelError,
            ops.pebble.APIError,
            ops.pebble.ChangeError,
            ops.pebble.ConnectionError,
            ops.pebble.TimeoutError,
        ) as error:
            raise ManagementUnavailableError(
                "Management operation completed but Verdaccio could not restart"
            ) from error
