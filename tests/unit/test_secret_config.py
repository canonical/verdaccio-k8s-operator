from dataclasses import replace
from pathlib import Path

import ops
import pytest
import yaml
from helpers import verdaccio_container
from ops import testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from secret_config import (
    PFX_PASSPHRASE_SECRET_OPTION,
    UPLINK_TOKENS_SECRET_OPTION,
    WEBHOOK_CREDENTIALS_SECRET_OPTION,
)
from workload import CONFIG_PATH, SERVICE_NAME


def test_all_credentials_are_loaded_from_secrets() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)
    uplink_secret = testing.Secret({"tokens": "npmjs: uplink-token"})
    webhook_secret = testing.Secret(
        {
            "credentials": (
                "notifications:\n"
                "  Authorization: Bearer notification-token\n"
                "notify:\n"
                "  https://hooks.example.test/audit:\n"
                "    X-Webhook-Key: webhook-token\n"
            )
        }
    )
    pfx_secret = testing.Secret({"passphrase": "pfx-passphrase"})
    config = {
        "uplinks-config": (
            "npmjs:\n  url: https://registry.npmjs.org/\n  auth:\n    type: bearer\n"
        ),
        "notifications-config": (
            "endpoint: https://hooks.example.test/packages\ncontent: 'published {{ name }}'\n"
        ),
        "notify-config": ("endpoint: https://hooks.example.test/audit\ncontent: '{{ name }}'\n"),
        "https-config": "pfx: /verdaccio/storage/server.pfx\n",
        UPLINK_TOKENS_SECRET_OPTION: uplink_secret.id,
        WEBHOOK_CREDENTIALS_SECRET_OPTION: webhook_secret.id,
        PFX_PASSPHRASE_SECRET_OPTION: pfx_secret.id,
    }
    state = testing.State(
        config=config,
        containers={container},
        storages={testing.Storage(STORAGE_NAME)},
        secrets={uplink_secret, webhook_secret, pfx_secret},
    )

    output = ctx.run(ctx.on.config_changed(), state)

    workload = output.get_container("verdaccio")
    config_path = workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")
    rendered = yaml.safe_load(config_path.read_text())
    assert rendered["uplinks"]["npmjs"]["auth"]["token"] == "uplink-token"
    assert rendered["notifications"]["headers"] == {"Authorization": "Bearer notification-token"}
    assert rendered["notify"]["headers"] == {"X-Webhook-Key": "webhook-token"}
    assert rendered["https"]["passphrase"] == "pfx-passphrase"
    assert config_path.stat().st_mode & 0o777 == 0o600
    assert output.unit_status == testing.ActiveStatus()
    exposed_surfaces = "\n".join(
        [output.unit_status.message, *(line.message for line in ctx.juju_log)]
    )
    for credential in (
        "uplink-token",
        "notification-token",
        "webhook-token",
        "pfx-passphrase",
    ):
        assert credential not in exposed_surfaces


def test_secret_changed_rotates_token_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = verdaccio_container(
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    secret = testing.Secret({"tokens": "npmjs: old-token"})
    first = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "uplinks-config": (
                    "npmjs:\n  url: https://registry.npmjs.org/\n  auth:\n    type: bearer\n"
                ),
                UPLINK_TOKENS_SECRET_OPTION: secret.id,
            },
            containers={container},
            storages={testing.Storage(STORAGE_NAME)},
            secrets={secret},
        ),
    )
    assert "old-token" in (config_dir / "config.yaml").read_text()

    restart_calls: list[tuple[str, ...]] = []
    original_restart = ops.Container.restart

    def record_restart(container: ops.Container, *service_names: str) -> None:
        restart_calls.append(service_names)
        original_restart(container, *service_names)

    monkeypatch.setattr(ops.Container, "restart", record_restart)
    rotated = replace(secret, latest_content={"tokens": "npmjs: new-token"})
    second = ctx.run(
        ctx.on.secret_changed(rotated),
        replace(first, secrets={rotated}),
    )

    config_text = (config_dir / "config.yaml").read_text()
    assert "new-token" in config_text
    assert "old-token" not in config_text
    assert restart_calls == [(SERVICE_NAME,)]

    tracked = next(item for item in second.secrets if item.id == secret.id)
    third = ctx.run(ctx.on.secret_changed(tracked), second)

    assert third.containers == second.containers
    assert restart_calls == [(SERVICE_NAME,)]


@pytest.mark.parametrize(
    ("config", "field"),
    [
        (
            {
                "uplinks-config": (
                    "npmjs:\n"
                    "  url: https://registry.npmjs.org/\n"
                    "  auth: {type: bearer, token: exposed-token}\n"
                )
            },
            "verdaccio.uplinks.npmjs.auth.token",
        ),
        (
            {
                "notifications-config": (
                    "endpoint: https://hooks.example.test/packages\n"
                    "content: published\n"
                    "headers: {Authorization: exposed-token}\n"
                )
            },
            "verdaccio.notifications.headers.Authorization",
        ),
        (
            {"https-config": ("pfx: /verdaccio/storage/server.pfx\npassphrase: exposed-token\n")},
            "verdaccio.https",
        ),
    ],
)
def test_credentials_in_ordinary_config_are_rejected(config: dict[str, str], field: str) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config=config,
            containers={verdaccio_container(can_connect=True)},
        ),
    )

    assert isinstance(output.unit_status, testing.BlockedStatus)
    assert field in output.unit_status.message
    assert "exposed-token" not in output.unit_status.message
    assert output.get_container("verdaccio").plan.services == {}


def test_unavailable_secret_blocks_without_exposing_its_id() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret_id = testing.Secret({"tokens": "unused"}).id

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={UPLINK_TOKENS_SECRET_OPTION: secret_id},
            containers={verdaccio_container(can_connect=True)},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        f"Secret unavailable: {UPLINK_TOKENS_SECRET_OPTION}"
    )
    assert secret_id not in output.unit_status.message
    assert output.get_container("verdaccio").plan.services == {}


def test_invalid_secret_content_blocks_without_exposing_content() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret({"tokens": "[invalid-secret"})

    output = ctx.run(
        ctx.on.collect_unit_status(),
        testing.State(
            config={UPLINK_TOKENS_SECRET_OPTION: secret.id},
            containers={verdaccio_container(can_connect=True)},
            secrets={secret},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        f"Invalid secret configuration: {UPLINK_TOKENS_SECRET_OPTION}"
    )
    assert "invalid-secret" not in output.unit_status.message


def test_collect_status_does_not_track_latest_secret_revision() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret(
        {"tokens": "npmjs: tracked-token"},
        latest_content={"tokens": "npmjs: latest-token"},
    )
    state = testing.State(
        config={
            "uplinks-config": (
                "npmjs:\n  url: https://registry.npmjs.org/\n  auth:\n    type: bearer\n"
            ),
            UPLINK_TOKENS_SECRET_OPTION: secret.id,
        },
        containers={verdaccio_container(can_connect=True)},
        secrets={secret},
    )

    output = ctx.run(ctx.on.collect_unit_status(), state)

    assert output.secrets == state.secrets
    assert output.unit_status == testing.WaitingStatus("Waiting for persistent storage")


@pytest.mark.parametrize(
    ("option", "secret_content", "config"),
    [
        (UPLINK_TOKENS_SECRET_OPTION, {"unexpected": "sensitive-value"}, {}),
        (
            UPLINK_TOKENS_SECRET_OPTION,
            {"tokens": "missing: sensitive-value"},
            {},
        ),
        (
            WEBHOOK_CREDENTIALS_SECRET_OPTION,
            {"credentials": "notifications:\n  Authorization: sensitive-value\n"},
            {},
        ),
        (
            WEBHOOK_CREDENTIALS_SECRET_OPTION,
            {
                "credentials": (
                    "notify:\n"
                    "  https://hooks.example.test/missing:\n"
                    "    Authorization: sensitive-value\n"
                )
            },
            {},
        ),
        (
            WEBHOOK_CREDENTIALS_SECRET_OPTION,
            {
                "credentials": (
                    "notify:\n"
                    "  https://hooks.example.test/missing:\n"
                    "    Authorization: sensitive-value\n"
                )
            },
            {
                "notify-config": (
                    "endpoint: https://hooks.example.test/configured\ncontent: published\n"
                )
            },
        ),
        (
            PFX_PASSPHRASE_SECRET_OPTION,
            {"passphrase": "sensitive-value"},
            {
                "https-config": (
                    "key: /verdaccio/storage/tls.key\ncert: /verdaccio/storage/tls.crt\n"
                )
            },
        ),
        (WEBHOOK_CREDENTIALS_SECRET_OPTION, {"credentials": "{}"}, {}),
    ],
)
def test_secret_target_mismatches_block_without_exposure(
    option: str,
    secret_content: dict[str, str],
    config: dict[str, str],
) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret(secret_content)
    state_config = {**config, option: secret.id}

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config=state_config,
            containers={verdaccio_container(can_connect=True)},
            secrets={secret},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(f"Invalid secret configuration: {option}")
    exposed_surfaces = "\n".join(
        [output.unit_status.message, *(line.message for line in ctx.juju_log)]
    )
    assert "sensitive-value" not in exposed_surfaces


def test_secret_headers_overlay_multiple_webhooks() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret(
        {
            "credentials": (
                "notify:\n"
                "  https://hooks.example.test/first:\n"
                "    Authorization: first-token\n"
                "  https://hooks.example.test/second:\n"
                "    Authorization: second-token\n"
            )
        }
    )
    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "notify-config": (
                    "- endpoint: https://hooks.example.test/first\n"
                    "  content: first\n"
                    "  packagePattern: first-*\n"
                    "- endpoint: https://hooks.example.test/second\n"
                    "  content: second\n"
                    "  packagePattern: second-*\n"
                    "- endpoint: https://hooks.example.test/public\n"
                    "  content: public\n"
                ),
                WEBHOOK_CREDENTIALS_SECRET_OPTION: secret.id,
            },
            containers={verdaccio_container(can_connect=True)},
            storages={testing.Storage(STORAGE_NAME)},
            secrets={secret},
        ),
    )

    workload = output.get_container("verdaccio")
    rendered = yaml.safe_load((workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text())
    assert rendered["notify"][0]["headers"] == {"Authorization": "first-token"}
    assert rendered["notify"][1]["headers"] == {"Authorization": "second-token"}
    assert "headers" not in rendered["notify"][2]


def test_duplicate_credentialed_webhook_endpoint_is_rejected() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret(
        {
            "credentials": (
                "notify:\n"
                "  https://hooks.example.test/shared:\n"
                "    Authorization: sensitive-value\n"
            )
        }
    )

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "notify-config": (
                    "- endpoint: https://hooks.example.test/shared\n"
                    "  content: first\n"
                    "  packagePattern: first-*\n"
                    "- endpoint: https://hooks.example.test/shared\n"
                    "  content: second\n"
                    "  packagePattern: second-*\n"
                ),
                WEBHOOK_CREDENTIALS_SECRET_OPTION: secret.id,
            },
            containers={verdaccio_container(can_connect=True)},
            secrets={secret},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        f"Invalid secret configuration: {WEBHOOK_CREDENTIALS_SECRET_OPTION}"
    )


def test_empty_uplink_token_mapping_preserves_omission() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    secret = testing.Secret({"tokens": "{}"})

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={
                "uplinks-config": "",
                UPLINK_TOKENS_SECRET_OPTION: secret.id,
            },
            containers={verdaccio_container(can_connect=True)},
            storages={testing.Storage(STORAGE_NAME)},
            secrets={secret},
        ),
    )

    workload = output.get_container("verdaccio")
    rendered = yaml.safe_load((workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text())
    assert "uplinks" not in rendered
