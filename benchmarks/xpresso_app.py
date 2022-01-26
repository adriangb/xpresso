from typing import Any, Dict

from starlette.requests import Request
from starlette.responses import Response

from benchmarks.constants import DAG_SHAPE, DELAY, NO_DELAY
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


dag_size, dep_without_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=NO_DELAY
)
print("/fast_deps dag size: ", dag_size)


async def fast_dependencies(
    _: Annotated[int, Dependant(dep_without_delays)]
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


dag_size, dep_with_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=DELAY
)
print("/slow_deps dag size: ", dag_size)


async def slow_dependencies(
    _: Annotated[int, Dependant(dep_with_delays)]
) -> Response:
    """An endpoint with dependencies that simulate IO"""
    return Response()


app = App(
    routes=[
        Path("/simple", get=simple),
        Path("/fast_deps", get=fast_dependencies),
        Path(
            "/slow_deps",
            get=Operation(
                slow_dependencies,
                execute_dependencies_concurrently=True,
            ),
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
