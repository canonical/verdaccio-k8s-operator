"""Validate charm configuration at a single typed boundary."""

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class CharmConfig(BaseModel):
    """Validated, immutable operator configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    log_level: Literal["debug", "info", "warning", "error"] = "info"


def config_input(config: Mapping[str, object]) -> dict[str, object]:
    """Adapt Juju configuration to plain model input."""
    return {"log_level": config.get("log-level", "info")}


def load_config(config: Mapping[str, object]) -> CharmConfig:
    """Validate the complete current configuration snapshot."""
    return CharmConfig.model_validate(config_input(config))


def validation_error_message(error: ValidationError) -> str:
    """Describe invalid fields without exposing their values."""
    fields = ", ".join(".".join(map(str, item["loc"])) for item in error.errors())
    return f"Invalid configuration: {fields}"
