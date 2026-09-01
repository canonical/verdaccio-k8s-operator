import json
from pathlib import Path

import ops
import pytest
import yaml
from ops import testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from workload import CONFIG_PATH, SERVICE_NAME


def _ingress_relation(url: str) -> testing.Relation:
    return testing.Relation(
        endpoint="ingress",
        interface="ingress",
        remote_app_name="traefik-k8s",
        remote_app_data={"ingress": json.dumps({"url": url})},
        remote_units_data={0: {}},
    )


def _ready_state(
    ingress: testing.Relation, *, config_dir: Path, url_prefix: str = ""
) -> testing.State:
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    return testing.State(
        leader=True,
        config={"url-prefix": url_prefix},
        containers={container},
        relations={ingress},
        storages={testing.Storage(STORAGE_NAME)},
    )


def test_ingress_relation_creation_publishes_configured_port(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    ingress = testing.Relation(
        endpoint="ingress",
        interface="ingress",
        remote_app_name="traefik-k8s",
    )
    config_dir = tmp_path / "created-conf"
    config_dir.mkdir()

    output = ctx.run(
        ctx.on.relation_created(ingress),
        _ready_state(ingress, config_dir=config_dir),
    )

    relation = output.get_relation(ingress.id)
    assert relation.local_app_data["port"] == "4873"
    assert relation.local_app_data["strip-prefix"] == "true"
    service = output.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert "VERDACCIO_PUBLIC_URL" not in service.environment


def test_root_ingress_publishes_port_and_public_url(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    ingress = _ingress_relation("https://registry.example.test/")
    config_dir = tmp_path / "root-conf"
    config_dir.mkdir()

    first = ctx.run(
        ctx.on.relation_changed(ingress, remote_unit=0),
        _ready_state(ingress, config_dir=config_dir),
    )
    second = ctx.run(ctx.on.config_changed(), first)

    relation = first.get_relation(ingress.id)
    assert relation.local_app_data["port"] == "4873"
    service = first.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert service.environment == {
        "HOME": "/opt/verdaccio",
        "VERDACCIO_PUBLIC_URL": "https://registry.example.test",
    }
    rendered = yaml.safe_load(
        (first.get_container("verdaccio").get_filesystem(ctx) / CONFIG_PATH.lstrip("/"))
        .read_text()
    )
    assert "url_prefix" not in rendered
    assert second.containers == first.containers
    assert second.get_relation(ingress.id).local_app_data == relation.local_app_data


def test_prefixed_ingress_converges_without_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    ingress = _ingress_relation("https://gateway.example.test/test-model-verdaccio-k8s")
    config_dir = tmp_path / "convergent-prefixed-conf"
    config_dir.mkdir()
    first = ctx.run(
        ctx.on.relation_changed(ingress, remote_unit=0),
        _ready_state(ingress, config_dir=config_dir),
    )
    restart_calls: list[tuple[str, ...]] = []
    original_restart = ops.Container.restart

    def record_restart(container: ops.Container, *service_names: str) -> None:
        restart_calls.append(service_names)
        original_restart(container, *service_names)

    monkeypatch.setattr(ops.Container, "restart", record_restart)
    second = ctx.run(ctx.on.config_changed(), first)

    rendered = yaml.safe_load(
        (second.get_container("verdaccio").get_filesystem(ctx) / CONFIG_PATH.lstrip("/"))
        .read_text()
    )
    assert rendered["url_prefix"] == "/test-model-verdaccio-k8s"
    assert second.containers == first.containers
    assert second.get_relation(ingress.id).local_app_data == first.get_relation(
        ingress.id
    ).local_app_data
    assert restart_calls == []


def test_prefixed_ingress_overrides_configured_public_prefix(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    ingress = _ingress_relation("https://gateway.example.test/test-model-verdaccio-k8s")
    config_dir = tmp_path / "prefixed-conf"
    config_dir.mkdir()

    related = ctx.run(
        ctx.on.relation_changed(ingress, remote_unit=0),
        _ready_state(ingress, config_dir=config_dir, url_prefix="/registry/"),
    )
    container = related.get_container("verdaccio")
    service = container.plan.services[SERVICE_NAME]
    assert service.environment["VERDACCIO_PUBLIC_URL"] == "https://gateway.example.test"
    rendered = yaml.safe_load(
        (container.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    )
    assert rendered["url_prefix"] == "/test-model-verdaccio-k8s"

    related_ingress = related.get_relation(ingress.id)
    unrelating = ctx.run(ctx.on.relation_broken(related_ingress), related)
    service = unrelating.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert "VERDACCIO_PUBLIC_URL" not in service.environment
    rendered = yaml.safe_load(
        (
            unrelating.get_container("verdaccio").get_filesystem(ctx)
            / CONFIG_PATH.lstrip("/")
        ).read_text()
    )
    assert rendered["url_prefix"] == "/registry/"
