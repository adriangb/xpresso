from typing import Any, Dict

from starlette.requests import Request
from starlette.responses import Response

from benchmarks.utils import generate_dag
from xpresso import App, Dependant, Operation, Path
from xpresso.typing import Annotated


def make_depends(type_: str, provider: str) -> str:
    return f"Annotated[{type_}, Dependant({provider})]"


glbls: Dict[str, Any] = {
    "Dependant": Dependant,
    "Annotated": Annotated,
}


async def simple(request: Request) -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


dep_without_delays = generate_dag(make_depends, glbls, 3, 2, 2, sleep=(0, 0))


async def fast_dependencies(
    _: Annotated[int, Dependant(dep_without_delays)]
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


# Establishing an asyncpg -> PostgreSQL connection takes ~75ms
# Running query takes about 1ms
# Hitting okta.com w/ httpx takes ~100ms
# So we'll take a range of 1ms to 100ms as delays for async dependencies
# And then make a medium sized DAG (3 levels, 2 deps per level, so 6 deps total)
dep_with_delays = generate_dag(make_depends, glbls, 3, 2, 2, sleep=(1e-3, 1e-1))


async def slow_dependencies(_: Annotated[int, Dependant(dep_with_delays)]) -> Response:
    """An endpoint with dependencies that simulate IO"""
    return Response()


app = App(
    routes=[
        Path("/simple", get=simple),
        Path("/fast_deps", get=fast_dependencies),
        Path(
            "/slow_deps",
            get=Operation(slow_dependencies, execute_dependencies_concurrently=True),
        ),
    ]
)


if __name__ == "__main__":
    # This is used for runing line_profiler
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        # for _ in range(100):
        #     client.get("/simple")
        for _ in range(100):
            client.get("/fast_deps")
