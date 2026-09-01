import os
from pathlib import Path

import yaml
from ops import pebble, testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from workload import CONFIG_PATH, SERVICE_NAME, WORKLOAD_USER_ID


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


def test_reconciliation_is_convergent(tmp_path: Path) -> None:
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

    second = ctx.run(ctx.on.config_changed(), first)

    assert second.containers == first.containers
    assert second.opened_ports == first.opened_ports
    assert second.unit_status == first.unit_status
    assert config_path.stat().st_mtime_ns == fixed_time


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
