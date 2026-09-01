import os
from dataclasses import replace
from pathlib import Path

import ops
import pytest
import yaml
from ops import pebble, testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from workload import CONFIG_PATH, HEALTH_CHECK_NAME, SERVICE_NAME, WORKLOAD_USER_ID


def test_pebble_ready_converges_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)
    storage = testing.Storage(STORAGE_NAME)

    output = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}, storages={storage}),
    )

    workload = output.get_container("verdaccio")
    assert workload.plan.services[SERVICE_NAME].command == (
        "verdaccio --config /verdaccio/conf/config.yaml --listen http://0.0.0.0:4873"
    )
    assert workload.plan.services[SERVICE_NAME].user_id == WORKLOAD_USER_ID
    assert workload.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE
    assert output.opened_ports == {testing.TCPPort(4873)}
    health_check = workload.plan.checks[HEALTH_CHECK_NAME]
    assert health_check.level is pebble.CheckLevel.READY
    assert health_check.http == {"url": "http://127.0.0.1:4873/-/ping"}
    assert health_check.period == "10s"
    assert health_check.timeout == "3s"
    assert health_check.threshold == 3
    assert output.unit_status == testing.ActiveStatus()
    config = (workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    assert yaml.safe_load(config)["log"]["level"] == "info"
    assert yaml.safe_load(config)["storage"] == "/verdaccio/storage"


def test_missing_container_is_waiting() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=False)
    storage = testing.Storage(STORAGE_NAME)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(containers={container}, storages={storage}),
    )

    assert output.unit_status == testing.WaitingStatus("Waiting for Verdaccio container")


def test_collect_status_checks_service_before_http_health() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)
    storage = testing.Storage(STORAGE_NAME)
    ready = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}, storages={storage}),
    )
    stopped_container = replace(
        ready.get_container("verdaccio"),
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.INACTIVE},
        check_infos={
            testing.CheckInfo(
                HEALTH_CHECK_NAME,
                level=pebble.CheckLevel.READY,
                status=pebble.CheckStatus.DOWN,
                failures=3,
                threshold=3,
            )
        },
    )

    output = ctx.run(
        ctx.on.collect_unit_status(),
        replace(ready, containers={stopped_container}),
    )

    assert output.unit_status == testing.MaintenanceStatus("Waiting for Verdaccio service")


def test_http_check_failure_and_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    storage = testing.Storage(STORAGE_NAME)
    started = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}, storages={storage}),
    )
    restart_calls: list[tuple[str, ...]] = []
    original_restart = ops.Container.restart

    def record_restart(container: ops.Container, *service_names: str) -> None:
        restart_calls.append(service_names)
        original_restart(container, *service_names)

    monkeypatch.setattr(ops.Container, "restart", record_restart)
    failed_check = testing.CheckInfo(
        HEALTH_CHECK_NAME,
        level=pebble.CheckLevel.READY,
        status=pebble.CheckStatus.DOWN,
        failures=3,
        threshold=3,
    )
    failed_container = replace(started.get_container("verdaccio"), check_infos={failed_check})
    failed = ctx.run(
        ctx.on.collect_unit_status(),
        replace(started, containers={failed_container}),
    )

    assert failed.unit_status == testing.MaintenanceStatus("Waiting for Verdaccio health check")

    recovered_check = testing.CheckInfo(
        HEALTH_CHECK_NAME,
        level=pebble.CheckLevel.READY,
        status=pebble.CheckStatus.UP,
        successes=1,
        threshold=3,
    )
    recovered_container = replace(failed.get_container("verdaccio"), check_infos={recovered_check})
    recovered = ctx.run(
        ctx.on.collect_unit_status(),
        replace(failed, containers={recovered_container}),
    )

    assert recovered.unit_status == testing.ActiveStatus()
    assert restart_calls == []


def test_upgrade_charm_adds_health_check(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    storage = testing.Storage(STORAGE_NAME)
    started = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}, storages={storage}),
    )
    started_container = started.get_container("verdaccio")
    legacy_layers: dict[str, pebble.Layer] = {}
    for label, layer in started_container.layers.items():
        layer_config = layer.to_dict()
        layer_config.pop("checks", None)
        legacy_layers[label] = pebble.Layer(layer_config)
    legacy_container = replace(started_container, layers=legacy_layers, check_infos=())

    upgraded = ctx.run(
        ctx.on.upgrade_charm(),
        replace(started, containers={legacy_container}),
    )

    assert upgraded.get_container("verdaccio").plan.checks[HEALTH_CHECK_NAME].http == {
        "url": "http://127.0.0.1:4873/-/ping"
    }
    assert upgraded.unit_status == testing.ActiveStatus()


def test_reconciliation_is_convergent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    storage = testing.Storage(STORAGE_NAME)

    first = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}, storages={storage}),
    )
    config_path = config_dir / "config.yaml"
    fixed_time = 1_700_000_000_000_000_000
    os.utime(config_path, ns=(fixed_time, fixed_time))
    pebble_calls: list[str] = []
    original_add_layer = ops.Container.add_layer
    original_replan = ops.Container.replan

    def record_add_layer(
        container: ops.Container,
        label: str,
        layer: str | pebble.LayerDict | pebble.Layer,
        *,
        combine: bool = False,
    ) -> None:
        pebble_calls.append("add_layer")
        original_add_layer(container, label, layer, combine=combine)

    def record_replan(container: ops.Container) -> None:
        pebble_calls.append("replan")
        original_replan(container)

    monkeypatch.setattr(ops.Container, "add_layer", record_add_layer)
    monkeypatch.setattr(ops.Container, "replan", record_replan)
    second = ctx.run(ctx.on.config_changed(), first)

    assert second.containers == first.containers
    assert second.opened_ports == first.opened_ports
    assert second.unit_status == first.unit_status
    assert config_path.stat().st_mtime_ns == fixed_time
    assert pebble_calls == []


def test_missing_storage_waits_without_mutating_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(ctx.on.config_changed(), testing.State(containers={container}))

    assert output.unit_status == testing.WaitingStatus("Waiting for persistent storage")
    assert output.get_container("verdaccio").plan.services == {}
    assert output.opened_ports == set()


def test_collect_status_reports_missing_storage() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(ctx.on.collect_unit_status(), testing.State(containers={container}))

    assert output.unit_status == testing.WaitingStatus("Waiting for persistent storage")


def test_storage_attached_converges_workload_and_preserves_data(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    storage = testing.Storage(STORAGE_NAME)
    storage_root = storage.get_filesystem(ctx)
    marker = storage_root / "private-package.json"
    marker.write_text('{"name":"private-package"}')
    config_root = tmp_path / "conf"
    config_root.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={
            "config": testing.Mount(location="/verdaccio/conf", source=config_root),
            STORAGE_NAME: testing.Mount(
                location="/verdaccio/storage",
                source=storage_root,
            ),
        },
    )

    first = ctx.run(
        ctx.on.storage_attached(storage),
        testing.State(containers={container}, storages={storage}),
    )
    second = ctx.run(ctx.on.config_changed(), first)

    workload_root = second.get_container("verdaccio").get_filesystem(ctx)
    assert (
        workload_root / "verdaccio/storage/private-package.json"
    ).read_text() == '{"name":"private-package"}'
    assert second.containers == first.containers
    assert second.unit_status == testing.ActiveStatus()
