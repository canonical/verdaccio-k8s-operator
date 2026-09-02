from helpers import verdaccio_container
from ops import testing

from charm import VerdaccioK8SCharm


def test_invalid_config_blocks_without_mutating_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"log-config": "level: verbose\n"},
            containers={container},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        "Invalid configuration: verdaccio.log.level"
    )
    assert output.get_container("verdaccio").plan.services == {}
    assert output.opened_ports == set()


def test_missing_storage_blocks_without_mutating_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"storage-path": ""},
            containers={container},
        ),
    )

    assert output.unit_status == testing.BlockedStatus("Invalid configuration: verdaccio")
    assert output.get_container("verdaccio").plan.services == {}


def test_invalid_yaml_blocks_without_mutating_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"packages-config": "["}, containers={container}),
    )

    assert output.unit_status == testing.BlockedStatus("Invalid configuration: verdaccio.packages")
    assert output.get_container("verdaccio").plan.services == {}


def test_collect_status_reports_nested_configuration_error() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.collect_unit_status(),
        testing.State(
            config={"server-config": "keepAliveTimeout: -1\n"},
            containers={container},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        "Invalid configuration: verdaccio.server.keepAliveTimeout"
    )


def test_all_numeric_non_ip_listen_address_is_rejected() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"listen-address": "1.2.3.4.5"}, containers={container}),
    )

    assert output.unit_status == testing.BlockedStatus("Invalid configuration: listen_address")
    assert output.get_container("verdaccio").plan.services == {}


def test_ingress_unsupported_maximum_port_is_blocked() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(config={"listen-port": 65535}, containers={container}),
    )

    assert output.unit_status == testing.BlockedStatus("Invalid configuration: listen_port")
    assert output.get_container("verdaccio").plan.services == {}
    assert output.opened_ports == set()


def test_metrics_middleware_override_is_rejected() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.config_changed(),
        testing.State(
            config={"middlewares-config": "metrics: {excludePaths: []}\n"},
            containers={container},
        ),
    )

    assert output.unit_status == testing.BlockedStatus(
        "Invalid configuration: verdaccio.middlewares"
    )
    assert output.get_container("verdaccio").plan.services == {}
