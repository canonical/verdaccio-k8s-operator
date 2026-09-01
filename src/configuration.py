"""Validate all charm and Verdaccio configuration at one typed boundary."""

import re
from collections.abc import Mapping
from ipaddress import ip_address
from typing import Annotated, Literal

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)


def _parse_yaml_fragment(value: object) -> object:
    """Parse one Juju string option into its Verdaccio section value."""
    if not isinstance(value, str):
        return value
    if not value.strip():
        return None
    try:
        return yaml.safe_load(value)
    except yaml.YAMLError as error:
        raise ValueError("must contain valid YAML") from error


def _as_tuple(value: object) -> object:
    """Freeze YAML sequences before strict model validation."""
    return tuple(value) if isinstance(value, list) else value


StringSequence = Annotated[tuple[str, ...], BeforeValidator(_as_tuple)]


class ConfigModel(BaseModel):
    """Closed, immutable base for operator-owned configuration schemas."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RateLimit(ConfigModel):
    """Request rate-limiting settings."""

    window_ms: int | None = Field(default=None, alias="windowMs", ge=1)
    max: int | None = Field(default=None, ge=1)


class WebConfig(ConfigModel):
    """Verdaccio web UI settings."""

    title: str | None = Field(default=None, min_length=1)
    logo: str | None = Field(default=None, min_length=1)
    logo_dark: str | None = Field(default=None, alias="logoDark", min_length=1)
    favicon: str | None = Field(default=None, min_length=1)
    gravatar: bool | None = None
    sort_packages: Literal["asc", "desc"] | None = None
    dark_mode: bool | None = Field(default=None, alias="darkMode")
    url_prefix: str | None = None
    language: str | None = Field(default=None, min_length=1)
    login: bool | None = None
    scope: str | None = None
    package_managers: StringSequence | None = Field(default=None, alias="pkgManagers")
    show_info: bool | None = Field(default=None, alias="showInfo")
    show_settings: bool | None = Field(default=None, alias="showSettings")
    show_search: bool | None = Field(default=None, alias="showSearch")
    show_footer: bool | None = Field(default=None, alias="showFooter")
    show_theme_switch: bool | None = Field(default=None, alias="showThemeSwitch")
    show_download_tarball: bool | None = Field(default=None, alias="showDownloadTarball")
    show_uplinks: bool | None = Field(default=None, alias="showUplinks")
    hide_deprecated_versions: bool | None = Field(default=None, alias="hideDeprecatedVersions")
    primary_color: str | None = Field(default=None, alias="primaryColor", min_length=1)
    show_raw: bool | None = Field(default=None, alias="showRaw")
    scripts_head: StringSequence | None = Field(default=None, alias="scriptsHead")
    scripts_body_after: StringSequence | None = Field(default=None, alias="scriptsBodyAfter")
    scripts_body_before: StringSequence | None = Field(default=None, alias="scriptsBodyBefore")
    meta_scripts: StringSequence | None = Field(default=None, alias="metaScripts")
    body_before: StringSequence | None = Field(default=None, alias="bodyBefore")
    body_after: StringSequence | None = Field(default=None, alias="bodyAfter")
    rate_limit: RateLimit | None = Field(default=None, alias="rateLimit")
    html_cache: bool | None = None
    enabled: bool | None = None


class UplinkAuth(ConfigModel):
    """Bearer or basic credentials for an uplink."""

    type: Literal["Bearer", "Basic", "bearer", "basic"]
    token: SecretStr | None = None
    token_env: bool | str | None = None

    @field_serializer("token")
    def serialize_token(self, token: SecretStr | None) -> str | None:
        """Reveal an uplink token only at the workload output boundary."""
        return token.get_secret_value() if token is not None else None


class UplinkConfig(ConfigModel):
    """Remote package registry settings."""

    url: str = Field(min_length=1)
    ca: str | None = None
    cache: bool | None = None
    timeout: str | int | float | None = None
    maxage: str | int | float | None = None
    max_fails: int | None = Field(default=None, ge=0)
    fail_timeout: str | int | float | None = None
    http_proxy: str | None = None
    https_proxy: str | None = None
    no_proxy: str | None = None
    headers: dict[str, str] | None = None
    auth: UplinkAuth | None = None
    strict_ssl: bool | None = None
    agent_options: dict[str, JsonValue] | None = None


class PackageAccess(ConfigModel):
    """Access policy for a package pattern."""

    storage: str | None = Field(default=None, min_length=1)
    publish: str | None = Field(default=None, min_length=1)
    proxy: str | None = Field(default=None, min_length=1)
    access: str | None = Field(default=None, min_length=1)
    unpublish: str | None = Field(default=None, min_length=1)


class HtpasswdConfig(ConfigModel):
    """Built-in htpasswd authentication settings."""

    file: str = Field(min_length=1)
    max_users: int | None = None
    algorithm: Literal["bcrypt", "md5", "sha1", "crypt"] | None = None
    rounds: int | None = Field(default=None, ge=4, le=31)
    slow_verify_ms: int | None = Field(default=None, ge=0)


class LoggerRedaction(ConfigModel):
    """Logger field-redaction settings."""

    paths: StringSequence = Field(min_length=1)
    censor: str | None = None
    remove: bool | None = None


class LoggerConfig(ConfigModel):
    """Verdaccio logger settings."""

    type: Literal["stdout", "file"] | None = None
    format: Literal["pretty", "pretty-timestamped", "json"] | None = None
    path: str | None = Field(default=None, min_length=1)
    level: Literal["fatal", "error", "warn", "info", "http", "debug", "trace"] | None = None
    colors: bool | None = None
    sync: bool | None = None
    redact: LoggerRedaction | None = None


class JwtOptions(ConfigModel):
    """JSON Web Token signing and verification options."""

    sign: dict[str, JsonValue] = Field(default_factory=dict)
    verify: dict[str, JsonValue] = Field(default_factory=dict)


class ApiSecurity(ConfigModel):
    """API token security settings."""

    legacy: bool | None = None
    migrate_to_secure_legacy_signature: bool | None = Field(
        default=None, alias="migrateToSecureLegacySignature"
    )
    jwt: JwtOptions | None = None


class SecurityConfig(ConfigModel):
    """Web and API token security settings."""

    web: JwtOptions | None = None
    api: ApiSecurity | None = None


class PublishConfig(ConfigModel):
    """Offline publication behavior."""

    allow_offline: bool | None = None
    keep_readmes: Literal["latest", "tagged", "all"] | None = None
    check_owners: bool | None = None


class HttpsKeyCert(ConfigModel):
    """PEM HTTPS certificate settings."""

    key: str = Field(min_length=1)
    cert: str = Field(min_length=1)
    ca: str | None = None


class HttpsPfx(ConfigModel):
    """PKCS#12 HTTPS certificate settings."""

    pfx: str = Field(min_length=1)
    passphrase: SecretStr | None = None

    @field_serializer("passphrase")
    def serialize_passphrase(self, passphrase: SecretStr | None) -> str | None:
        """Reveal the passphrase only at the workload output boundary."""
        return passphrase.get_secret_value() if passphrase is not None else None


class NotificationConfig(ConfigModel):
    """Package publication notification settings."""

    endpoint: str = Field(min_length=1)
    content: str
    package_pattern: str | None = Field(default=None, alias="packagePattern")
    package_pattern_flags: str | None = Field(default=None, alias="packagePatternFlags")
    method: str | None = Field(default=None, min_length=1)
    headers: dict[str, str] | None = None


class LegacyAuthCache(ConfigModel):
    """Legacy bearer-token cache settings."""

    enabled: bool | None = None
    max_entries: int | None = Field(default=None, alias="maxEntries", ge=1)
    ttl_ms: int | None = Field(default=None, alias="ttlMs", ge=1)


class ServerConfig(ConfigModel):
    """HTTP server settings not owned by the charm listener."""

    rate_limit: RateLimit | None = Field(default=None, alias="rateLimit")
    keep_alive_timeout: int | None = Field(default=None, alias="keepAliveTimeout", ge=0)
    legacy_auth_cache: LegacyAuthCache | None = Field(default=None, alias="legacyAuthCache")
    plugin_prefix: str | None = Field(default=None, alias="pluginPrefix", min_length=1)
    password_validation_regex: str | None = Field(
        default=None, alias="passwordValidationRegex", min_length=1
    )
    trust_proxy: str | int | bool | None = Field(default=None, alias="trustProxy")
    search_remote: bool | None = Field(default=None, alias="searchRemote")


class FlagsConfig(ConfigModel):
    """Verdaccio 6 feature flags."""

    search_remote: bool | None = Field(default=None, alias="searchRemote")
    change_password: bool | None = Field(default=None, alias="changePassword")
    create_user: bool | None = Field(default=None, alias="createUser")
    web_login: bool | None = Field(default=None, alias="webLogin")


class I18nConfig(ConfigModel):
    """Internationalization settings."""

    web: str = Field(min_length=1)


class VerdaccioConfig(ConfigModel):
    """Complete user-facing Verdaccio 6 configuration schema."""

    storage: str | None = Field(default=None, min_length=1)
    plugins: str | None = Field(default=None, min_length=1)
    web: Annotated[WebConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    auth: Annotated[dict[str, JsonValue] | None, BeforeValidator(_parse_yaml_fragment)] = None
    uplinks: Annotated[dict[str, UplinkConfig] | None, BeforeValidator(_parse_yaml_fragment)] = (
        None
    )
    packages: Annotated[dict[str, PackageAccess] | None, BeforeValidator(_parse_yaml_fragment)] = (
        None
    )
    server: Annotated[ServerConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    publish: Annotated[PublishConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    url_prefix: str | None = None
    security: Annotated[SecurityConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    user_rate_limit: Annotated[RateLimit | None, BeforeValidator(_parse_yaml_fragment)] = Field(
        default=None, alias="userRateLimit"
    )
    max_body_size: str | None = Field(default=None, min_length=1)
    https: Annotated[HttpsKeyCert | HttpsPfx | None, BeforeValidator(_parse_yaml_fragment)] = None
    user_agent: str | bool | None = None
    http_proxy: str | None = None
    https_proxy: str | None = None
    no_proxy: str | None = None
    store: Annotated[dict[str, JsonValue] | None, BeforeValidator(_parse_yaml_fragment)] = None
    notifications: Annotated[NotificationConfig | None, BeforeValidator(_parse_yaml_fragment)] = (
        None
    )
    notify: Annotated[
        NotificationConfig
        | Annotated[tuple[NotificationConfig, ...], BeforeValidator(_as_tuple)]
        | None,
        BeforeValidator(_parse_yaml_fragment),
    ] = None
    middlewares: Annotated[dict[str, JsonValue] | None, BeforeValidator(_parse_yaml_fragment)] = (
        None
    )
    filters: Annotated[dict[str, JsonValue] | None, BeforeValidator(_parse_yaml_fragment)] = None
    log: Annotated[LoggerConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    flags: Annotated[FlagsConfig | None, BeforeValidator(_parse_yaml_fragment)] = None
    i18n: Annotated[I18nConfig | None, BeforeValidator(_parse_yaml_fragment)] = None

    @field_validator("auth")
    @classmethod
    def validate_builtin_auth(
        cls, auth: dict[str, JsonValue] | None
    ) -> dict[str, JsonValue] | None:
        """Validate the built-in plugin while preserving third-party plugin schemas."""
        if auth is not None and "htpasswd" in auth:
            HtpasswdConfig.model_validate(auth["htpasswd"])
        return auth

    @model_validator(mode="after")
    def require_storage(self) -> "VerdaccioConfig":
        """Require either local storage or a configured storage plugin."""
        if self.storage is None and self.store is None:
            raise ValueError("storage or store must be configured")
        return self

    def as_yaml(self) -> str:
        """Serialize the validated model to the exact workload YAML shape."""
        data = self.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


class CharmConfig(ConfigModel):
    """Validated, immutable operator configuration."""

    verdaccio: VerdaccioConfig
    listen_protocol: Literal["http", "https"]
    listen_address: str = Field(min_length=1)
    listen_port: int = Field(ge=1, le=65535)

    @field_validator("listen_protocol")
    @classmethod
    def require_https_config(
        cls, protocol: Literal["http", "https"], info: ValidationInfo
    ) -> Literal["http", "https"]:
        """Require certificate settings before enabling HTTPS."""
        verdaccio = info.data.get("verdaccio")
        if (
            protocol == "https"
            and isinstance(verdaccio, VerdaccioConfig)
            and verdaccio.https is None
        ):
            raise ValueError("requires https-config when listen-protocol is https")
        return protocol

    @field_validator("listen_address")
    @classmethod
    def validate_listen_address(cls, address: str) -> str:
        """Accept IP literals or DNS hostnames without shell metacharacters."""
        candidate = address.removeprefix("[").removesuffix("]")
        try:
            return str(ip_address(candidate))
        except ValueError:
            hostname = candidate.removesuffix(".")
            labels = hostname.split(".")
            valid_hostname = (
                bool(hostname)
                and len(hostname) <= 253
                and not all(label.isdigit() for label in labels)
                and all(
                    re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                    for label in labels
                )
            )
            if not valid_hostname:
                raise ValueError("must be an IP address or DNS hostname")
            return candidate


def _optional_string(value: object) -> object:
    """Omit blank scalar options from the generated Verdaccio configuration."""
    return None if value == "" else value


def _user_agent_input(value: object) -> object:
    """Decode the boolean spellings accepted by Verdaccio's user_agent setting."""
    if value == "true":
        return True
    if value == "false":
        return False
    return _optional_string(value)


def config_input(config: Mapping[str, object]) -> dict[str, object]:
    """Assemble a complete Juju snapshot after charmcraft defaults are applied."""
    verdaccio = {
        "storage": _optional_string(config.get("storage-path")),
        "plugins": _optional_string(config.get("plugins-path")),
        "web": config.get("web-config"),
        "auth": config.get("auth-config"),
        "uplinks": config.get("uplinks-config"),
        "packages": config.get("packages-config"),
        "server": config.get("server-config"),
        "publish": config.get("publish-config"),
        "url_prefix": _optional_string(config.get("url-prefix")),
        "security": config.get("security-config"),
        "userRateLimit": config.get("user-rate-limit-config"),
        "max_body_size": _optional_string(config.get("max-body-size")),
        "https": config.get("https-config"),
        "user_agent": _user_agent_input(config.get("user-agent")),
        "http_proxy": _optional_string(config.get("http-proxy")),
        "https_proxy": _optional_string(config.get("https-proxy")),
        "no_proxy": _optional_string(config.get("no-proxy")),
        "store": config.get("store-config"),
        "notifications": config.get("notifications-config"),
        "notify": config.get("notify-config"),
        "middlewares": config.get("middlewares-config"),
        "filters": config.get("filters-config"),
        "log": config.get("log-config"),
        "flags": config.get("flags-config"),
        "i18n": config.get("i18n-config"),
    }
    return {
        "verdaccio": verdaccio,
        "listen_address": config.get("listen-address"),
        "listen_protocol": config.get("listen-protocol"),
        "listen_port": config.get("listen-port"),
    }


def load_config(config: Mapping[str, object]) -> CharmConfig:
    """Validate the complete current configuration snapshot."""
    return CharmConfig.model_validate(config_input(config))


def validation_error_message(error: ValidationError) -> str:
    """Describe invalid fields without exposing their values."""
    fields = ", ".join(".".join(map(str, item["loc"])) for item in error.errors())
    return f"Invalid configuration: {fields}"
