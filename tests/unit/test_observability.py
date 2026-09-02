import json
from dataclasses import replace
from pathlib import Path

import ops
import pytest
from helpers import verdaccio_container
from ops import pebble, testing

from charm import STORAGE_NAME, VerdaccioK8SCharm
from workload import SERVICE_NAME

LOKI_PUSH_URL = "http://loki-k8s-0.loki-k8s-endpoints:3100/loki/api/v1/push"


def _logging_relation() -> testing.Relation:
    return testing.Relation(
        endpoint="logging",
        interface="loki_push_api",
        remote_app_name="loki-k8s",
        remote_units_data={
            0: {"endpoint": json.dumps({"url": LOKI_PUSH_URL})},
        },
    )


def test_logging_relation_recovers_with_pebble_and_converges() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    logging = _logging_relation()
    disconnected = verdaccio_container(can_connect=False)
    initial = testing.State(
        leader=True,
        containers={disconnected},
        relations={logging},
        model=testing.Model(
            name="test-model",
            uuid="00000000-0000-4000-8000-000000000000",
        ),
        storages={testing.Storage(STORAGE_NAME)},
    )

    unavailable = ctx.run(
        ctx.on.relation_changed(logging, remote_unit=0),
        initial,
    )
    assert "log-targets" not in unavailable.get_container("verdaccio").plan.to_dict()

    connected = replace(unavailable.get_container("verdaccio"), can_connect=True)
    first = ctx.run(
        ctx.on.pebble_ready(connected),
        replace(unavailable, containers={connected}),
    )
    related_logging = first.get_relation(logging.id)
    second = ctx.run(
        ctx.on.relation_changed(related_logging, remote_unit=0),
        first,
    )
    metadata = json.loads(second.get_relation(logging.id).local_app_data["metadata"])
    assert metadata["application"] == "verdaccio-k8s"

    workload = first.get_container("verdaccio")
    log_targets = workload.plan.to_dict().get("log-targets")
    assert log_targets is not None
    target = log_targets["loki-k8s/0"]
    assert target == {
        "override": "replace",
        "type": "loki",
        "location": LOKI_PUSH_URL,
        "services": ["all"],
        "labels": {
            "product": "Juju",
            "charm": "verdaccio-k8s",
            "juju_model": "test-model",
            "juju_model_uuid": "00000000-0000-4000-8000-000000000000",
            "juju_application": "verdaccio-k8s",
            "juju_unit": "verdaccio-k8s/0",
            "job": "juju_test-model_00000000_verdaccio-k8s",
        },
    }
    assert workload.service_statuses[SERVICE_NAME] is pebble.ServiceStatus.ACTIVE
    assert first.unit_status == testing.ActiveStatus()
    assert second.containers == first.containers
    assert second.unit_status == first.unit_status


def _metrics_relation() -> testing.Relation:
    return testing.Relation(
        endpoint="metrics-endpoint",
        interface="prometheus_scrape",
        remote_app_name="prometheus-k8s",
        remote_units_data={0: {}},
    )


def _tracing_relation(url: str, *, protocol: str = "otlp_http") -> testing.Relation:
    return testing.Relation(
        endpoint="tracing",
        interface="tracing",
        remote_app_name="tempo-k8s",
        remote_app_data={
            "receivers": json.dumps(
                [
                    {
                        "protocol": {"name": protocol, "type": "http"},
                        "url": url,
                    }
                ]
            )
        },
        remote_units_data={0: {}},
    )


def test_metrics_relation_publishes_internal_scrape_job_and_converges(
    tmp_path: Path,
) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    metrics = _metrics_relation()
    config_dir = tmp_path / "metrics-conf"
    config_dir.mkdir()
    container = verdaccio_container(
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    initial = testing.State(
        leader=True,
        containers={container},
        relations={metrics},
        storages={testing.Storage(STORAGE_NAME)},
    )

    first = ctx.run(ctx.on.pebble_ready(container), initial)
    first_app_data = first.get_relation(metrics.id).local_app_data
    second = ctx.run(ctx.on.config_changed(), first)

    related_metrics = second.get_relation(metrics.id)
    assert json.loads(related_metrics.local_app_data["scrape_jobs"]) == [
        {
            "metrics_path": "/metrics",
            "static_configs": [{"targets": ["*:9464"]}],
        }
    ]
    metadata = json.loads(related_metrics.local_app_data["scrape_metadata"])
    assert metadata["application"] == "verdaccio-k8s"
    assert second.opened_ports == {testing.TCPPort(4873)}
    assert second.containers == first.containers
    assert related_metrics.local_app_data == first_app_data
    assert second.unit_status == testing.ActiveStatus()


def test_tracing_relation_updates_and_removes_otlp_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    tracing = _tracing_relation("http://tempo-k8s:4318")
    config_dir = tmp_path / "tracing-conf"
    config_dir.mkdir()
    container = verdaccio_container(
        can_connect=True,
        mounts={"config": testing.Mount(location="/verdaccio/conf", source=config_dir)},
    )
    initial = testing.State(
        leader=True,
        containers={container},
        relations={tracing},
        storages={testing.Storage(STORAGE_NAME)},
    )

    related = ctx.run(
        ctx.on.relation_changed(tracing, remote_unit=0),
        initial,
    )
    service = related.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert service.environment["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://tempo-k8s:4318/"
    assert service.environment["OTEL_SERVICE_NAME"] == "verdaccio-k8s"
    assert json.loads(related.get_relation(tracing.id).local_app_data["receivers"]) == [
        "otlp_http"
    ]

    restart_calls: list[tuple[str, ...]] = []
    original_restart = ops.Container.restart

    def record_restart(container: ops.Container, *service_names: str) -> None:
        restart_calls.append(service_names)
        original_restart(container, *service_names)

    monkeypatch.setattr(ops.Container, "restart", record_restart)
    second = ctx.run(ctx.on.config_changed(), related)
    assert second.containers == related.containers
    assert restart_calls == []

    related_tracing = second.get_relation(tracing.id)
    removed = ctx.run(ctx.on.relation_broken(related_tracing), second)
    service = removed.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in service.environment
    assert service.environment["NODE_OPTIONS"] == (
        "--require /opt/verdaccio-app/dist/instrumentation.js"
    )
    assert removed.unit_status == testing.ActiveStatus()


def test_invalid_optional_tracing_endpoint_does_not_block_workload() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    tracing = _tracing_relation("not-a-url")
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.relation_changed(tracing, remote_unit=0),
        testing.State(
            leader=True,
            containers={container},
            relations={tracing},
            storages={testing.Storage(STORAGE_NAME)},
        ),
    )

    service = output.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in service.environment
    assert output.unit_status == testing.ActiveStatus()


def test_follower_ignores_tracing_protocol_before_leader_request() -> None:
    ctx = testing.Context(VerdaccioK8SCharm)
    tracing = _tracing_relation("http://tempo-k8s:9411", protocol="zipkin")
    container = verdaccio_container(can_connect=True)

    output = ctx.run(
        ctx.on.relation_changed(tracing, remote_unit=0),
        testing.State(
            leader=False,
            containers={container},
            relations={tracing},
            storages={testing.Storage(STORAGE_NAME)},
        ),
    )

    service = output.get_container("verdaccio").plan.services[SERVICE_NAME]
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in service.environment
    assert output.unit_status == testing.ActiveStatus()
