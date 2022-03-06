from typing import Any, Dict, Mapping, Union, List

from starlette.routing import BaseRoute, Route

from xpresso import App, Depends, Operation, Path, Request, Response, Router, FromQuery, FromPath
from xpresso.routing.mount import Mount
from xpresso.typing import Annotated

from benchmarks.constants import DAG_SHAPE, DELAY, NO_DELAY, ROUTING_PATHS
from benchmarks.utils import generate_dag

def make_depends(type_: str, provider: str) -> str:
    return f"Annotated[{type_}, Depends({provider})]"


glbls: Dict[str, Any] = {
    "Depends": Depends,
    "Annotated": Annotated,
}


def simple(request: Request) -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


dag_size, dep_without_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=NO_DELAY
)
print("/fast_deps dag size: ", dag_size)


def fast_dependencies(
    _: Annotated[int, Depends(dep_without_delays)]
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


dag_size, dep_with_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=DELAY
)
print("/slow_deps dag size: ", dag_size)


def slow_dependencies(
    _: Annotated[int, Depends(dep_with_delays)]
) -> Response:
    """An endpoint with dependencies that simulate IO"""
    return Response()


Paths = Mapping[str, Union["Paths", None]]  # type: ignore[misc]


def recurisively_generate_routes(paths: Paths) -> Router:
    routes: List[BaseRoute] = []
    for path in paths:
        subpaths = paths[path]
        if subpaths is None:
            routes.append(Route(f"/{path}", simple))
        else:
            routes.append(Mount(f"/{path}", app=recurisively_generate_routes(subpaths)))
    return Router(routes=routes)


async def parameters(
    p1: FromPath[str],
    p2: FromPath[int],
    q1: FromQuery[str],
    q2: FromQuery[int],
) -> Response:
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
        Mount("/routing", app=recurisively_generate_routes(ROUTING_PATHS)),
        Path("/parameters/{p1}/{p2}", get=parameters)
    ]
)
