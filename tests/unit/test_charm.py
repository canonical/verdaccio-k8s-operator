import os
from pathlib import Path

from ops import pebble, testing

from charm import COMMAND, CONFIG_PATH, PORT, SERVICE_NAME, VerdaccioK8SCharm


def test_pebble_ready_converges_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.pebble_ready(container),
        testing.State(containers={container}),
    )

    workload = output.get_container("verdaccio")
    assert workload.plan.services[SERVICE_NAME].command == COMMAND
    assert workload.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE
    assert output.opened_ports == {testing.TCPPort(PORT)}
    assert output.unit_status == testing.ActiveStatus()
    config = (workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    assert "level: info" in config
    assert "storage: /verdaccio/storage" in config


def test_invalid_config_blocks_without_mutating_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"log-level": "verbose"}, containers={container}),
    )

    assert output.unit_status == testing.BlockedStatus("Invalid configuration: log_level")
    assert output.get_container("verdaccio").plan.services == {}
    assert output.opened_ports == set()


def test_missing_container_is_waiting() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = testing.Container("verdaccio", can_connect=False)

    output = ctx.run(ctx.on.config_changed(), testing.State(containers={container}))

    assert output.unit_status == testing.WaitingStatus("Waiting for Verdaccio container")


def test_log_level_change_restarts_service(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    initial = ctx.run(ctx.on.pebble_ready(container), testing.State(containers={container}))

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"log-level": "debug"},
            containers=initial.containers,
            opened_ports=initial.opened_ports,
        ),
    )

    workload = output.get_container("verdaccio")
    config = (workload.get_filesystem(ctx) / CONFIG_PATH.lstrip("/")).read_text()
    assert "level: debug" in config
    assert workload.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE
    assert output.unit_status == testing.ActiveStatus()


def test_reconciliation_is_convergent(tmp_path: Path) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    container = testing.Container(
        "verdaccio",
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    first = ctx.run(ctx.on.pebble_ready(container), testing.State(containers={container}))
    config_path = config_dir / "config.yaml"
    fixed_time = 1_700_000_000_000_000_000
    os.utime(config_path, ns=(fixed_time, fixed_time))

    second = ctx.run(ctx.on.config_changed(), first)

    assert second.containers == first.containers
    assert second.opened_ports == first.opened_ports
    assert second.unit_status == first.unit_status
    assert config_path.stat().st_mtime_ns == fixed_time
