from collections.abc import Mapping

from ops import testing


def verdaccio_container(
    *,
    can_connect: bool,
    mounts: Mapping[str, testing.Mount] | None = None,
    version_stdout: str = "v6.10.1\n",
    version_return_code: int = 0,
) -> testing.Container:
    """Build a Verdaccio container with the workload's standard executable behavior."""
    return testing.Container(
        "verdaccio",
        can_connect=can_connect,
        mounts=mounts or {},
        execs={
            testing.Exec(
                ["verdaccio", "--version"],
                stdout=version_stdout,
                return_code=version_return_code,
            )
        },
    )
