"""Resolve, validate, and apply user-provided Juju secret configuration."""

from collections.abc import Mapping
from typing import Annotated, Self

import ops
import yaml
from pydantic import BeforeValidator, Field, SecretStr, ValidationError, model_validator

from config import (
    CharmConfig,
    ConfigModel,
    HttpsPfx,
    NotificationConfig,
    VerdaccioConfig,
    load_config,
)

UPLINK_TOKENS_SECRET_OPTION = "uplink-tokens-secret-id"
WEBHOOK_CREDENTIALS_SECRET_OPTION = "webhook-credentials-secret-id"
PFX_PASSPHRASE_SECRET_OPTION = "pfx-passphrase-secret-id"
_SECRET_CONTENT_KEYS = {
    UPLINK_TOKENS_SECRET_OPTION: "tokens",
    WEBHOOK_CREDENTIALS_SECRET_OPTION: "credentials",
    PFX_PASSPHRASE_SECRET_OPTION: "passphrase",
}


class SecretConfigurationError(Exception):
    """A secret is unavailable, invalid, or does not match public configuration."""

    def __init__(self, option: str, *, unavailable: bool = False) -> None:
        self.option = option
        self.unavailable = unavailable
        super().__init__(option)

    @property
    def status_message(self) -> str:
        """Return an actionable message containing no secret identifier or value."""
        prefix = "Secret unavailable" if self.unavailable else "Invalid secret configuration"
        return f"{prefix}: {self.option}"


def _parse_yaml_fragment(value: object) -> object:
    """Parse a structured string stored as one Juju secret value."""
    if not isinstance(value, str):
        return value
    try:
        return yaml.safe_load(value)
    except yaml.YAMLError as error:
        raise ValueError("must contain valid YAML") from error


class WebhookCredentials(ConfigModel):
    """Secret HTTP headers for configured publication webhooks."""

    notifications: dict[str, SecretStr] | None = None
    notify: dict[str, dict[str, SecretStr]] | None = None

    @model_validator(mode="after")
    def require_headers(self) -> Self:
        """Reject an empty webhook credential document."""
        if self.notifications is None and self.notify is None:
            raise ValueError("notifications or notify headers are required")
        return self


class SecretConfig(ConfigModel):
    """Validated values acquired from user-provided Juju secrets."""

    uplink_tokens: Annotated[
        dict[str, SecretStr] | None, BeforeValidator(_parse_yaml_fragment)
    ] = Field(default=None, alias=UPLINK_TOKENS_SECRET_OPTION)
    webhook_credentials: Annotated[
        WebhookCredentials | None, BeforeValidator(_parse_yaml_fragment)
    ] = Field(default=None, alias=WEBHOOK_CREDENTIALS_SECRET_OPTION)
    pfx_passphrase: SecretStr | None = Field(default=None, alias=PFX_PASSPHRASE_SECRET_OPTION)


def _resolve_secret_input(
    model: ops.Model, config: Mapping[str, object], *, refresh: bool
) -> dict[str, str]:
    """Translate configured secret IDs into plain values at the framework boundary."""
    result: dict[str, str] = {}
    for option, content_key in _SECRET_CONTENT_KEYS.items():
        secret_id = config.get(option)
        if not secret_id:
            continue
        try:
            content = model.get_secret(id=str(secret_id)).get_content(refresh=refresh)
        except ops.ModelError as error:
            raise SecretConfigurationError(option, unavailable=True) from error
        if content_key not in content:
            raise SecretConfigurationError(option)
        result[option] = content[content_key]
    return result


def _load_secret_config(secret_input: Mapping[str, object]) -> SecretConfig:
    """Validate resolved contents and map failures back to their public option."""
    try:
        return SecretConfig.model_validate(secret_input)
    except ValidationError as error:
        option = str(error.errors()[0]["loc"][0])
        raise SecretConfigurationError(option) from error


def _apply_uplink_tokens(
    verdaccio: VerdaccioConfig, tokens: dict[str, SecretStr]
) -> VerdaccioConfig:
    """Attach secret tokens to configured uplink authentication blocks."""
    uplinks = dict(verdaccio.uplinks or {})
    for name, token in tokens.items():
        uplink = uplinks.get(name)
        if uplink is None or uplink.auth is None:
            raise SecretConfigurationError(UPLINK_TOKENS_SECRET_OPTION)
        auth = uplink.auth.model_copy(update={"token": token})
        uplinks[name] = uplink.model_copy(update={"auth": auth})
    return verdaccio.model_copy(update={"uplinks": uplinks})


def _apply_webhook_credentials(
    verdaccio: VerdaccioConfig, credentials: WebhookCredentials
) -> VerdaccioConfig:
    """Attach secret headers to configured webhook endpoints."""
    notifications = verdaccio.notifications
    if credentials.notifications is not None:
        if notifications is None:
            raise SecretConfigurationError(WEBHOOK_CREDENTIALS_SECRET_OPTION)
        notifications = notifications.model_copy(update={"headers": credentials.notifications})

    notify = verdaccio.notify
    if credentials.notify is not None:
        if notify is None:
            raise SecretConfigurationError(WEBHOOK_CREDENTIALS_SECRET_OPTION)
        webhooks = (notify,) if isinstance(notify, NotificationConfig) else notify
        credential_endpoints = set(credentials.notify)
        configured_endpoints = {webhook.endpoint for webhook in webhooks}
        matched_endpoints = [
            webhook.endpoint for webhook in webhooks if webhook.endpoint in credential_endpoints
        ]
        if not credential_endpoints <= configured_endpoints or len(matched_endpoints) != len(
            set(matched_endpoints)
        ):
            raise SecretConfigurationError(WEBHOOK_CREDENTIALS_SECRET_OPTION)
        updated_webhooks = tuple(
            webhook.model_copy(update={"headers": credentials.notify[webhook.endpoint]})
            if webhook.endpoint in credentials.notify
            else webhook
            for webhook in webhooks
        )
        notify = (
            updated_webhooks[0] if isinstance(notify, NotificationConfig) else updated_webhooks
        )

    return verdaccio.model_copy(update={"notifications": notifications, "notify": notify})


def _apply_secret_config(config: CharmConfig, secrets: SecretConfig) -> CharmConfig:
    """Overlay credentials onto their validated public configuration targets."""
    verdaccio = config.verdaccio
    if secrets.uplink_tokens:
        verdaccio = _apply_uplink_tokens(verdaccio, secrets.uplink_tokens)
    if secrets.webhook_credentials is not None:
        verdaccio = _apply_webhook_credentials(verdaccio, secrets.webhook_credentials)
    if secrets.pfx_passphrase is not None:
        if not isinstance(verdaccio.https, HttpsPfx):
            raise SecretConfigurationError(PFX_PASSPHRASE_SECRET_OPTION)
        https = verdaccio.https.model_copy(update={"passphrase": secrets.pfx_passphrase})
        verdaccio = verdaccio.model_copy(update={"https": https})
    return config.model_copy(update={"verdaccio": verdaccio})


def load_secret_backed_config(
    model: ops.Model, config: Mapping[str, object], *, refresh: bool = True
) -> CharmConfig:
    """Validate public config, resolve secrets, then assemble effective config."""
    validated = load_config(config)
    secret_input = _resolve_secret_input(model, config, refresh=refresh)
    secrets = _load_secret_config(secret_input)
    return _apply_secret_config(validated, secrets)
