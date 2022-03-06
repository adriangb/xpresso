from typing import Mapping, List, Union

from fastapi import FastAPI as App, Response, Request, Depends, Query, Path
from fastapi.routing import Mount, APIRouter as Router, APIRoute
from starlette.routing import BaseRoute, Route

from benchmarks.constants import DAG_SHAPE, DELAY, NO_DELAY, ROUTING_PATHS
from benchmarks.utils import generate_dag


def make_depends(type_: str, provider: str) -> str:
    return f"{type_} = Depends({provider})"


glbls = {"Depends": Depends}


async def simple(request: Request) -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


dag_size, dep_without_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=NO_DELAY
)
print("/fast_deps dag size: ", dag_size)


async def fast_dependencies(
    _: int = Depends(dep_without_delays),
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


dag_size, dep_with_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=DELAY
)
print("/slow_deps dag size: ", dag_size)


async def slow_dependencies(
    _: int = Depends(dep_with_delays),
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
    p1: str = Path(...),
    p2: int = Path(...),
    q1: str = Query(...),
    q2: int = Query(...),
) -> Response:
    return Response()


app = App(
    routes=[
        APIRoute("/simple", simple),
        APIRoute("/fast_deps", fast_dependencies),
        APIRoute(
            "/slow_deps",
            slow_dependencies,
        ),
        Mount("/routing", app=recurisively_generate_routes(ROUTING_PATHS)),
        APIRoute("/parameters/{p1}/{p2}", parameters),
    ]
)
