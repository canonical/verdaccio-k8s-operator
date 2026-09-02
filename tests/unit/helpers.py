from collections.abc import Iterable, Mapping

from ops import pebble, testing


def verdaccio_container(
    *,
    can_connect: bool,
    mounts: Mapping[str, testing.Mount] | None = None,
    version_stdout: str = "v6.10.1\n",
    version_return_code: int = 0,
    execs: Iterable[testing.Exec] = (),
    service_statuses: Mapping[str, pebble.ServiceStatus] | None = None,
) -> testing.Container:
    """Build a Verdaccio container with the workload's standard executable behavior."""
    default_exec = testing.Exec(
        ["verdaccio", "--version"],
        stdout=version_stdout,
        return_code=version_return_code,
    )
    execs_by_command = {default_exec.command_prefix: default_exec}
    execs_by_command.update({execution.command_prefix: execution for execution in execs})
    return testing.Container(
        "verdaccio",
        can_connect=can_connect,
        mounts=mounts or {},
        service_statuses=service_statuses or {},
        execs=frozenset(execs_by_command.values()),
    )
