from fastapi import Depends
from fastapi import FastAPI as App
from starlette.responses import Response

from benchmarks.constants import DAG_SHAPE, DELAY, NO_DELAY
from benchmarks.utils import generate_dag

app = App()


def make_depends(type_: str, provider: str) -> str:
    return f"{type_} = Depends({provider})"


glbls = {"Depends": Depends}


@app.router.get("/simple")
async def simple() -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


dag_size, dep_without_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=NO_DELAY
)
print("/fast_deps dag size: ", dag_size)


@app.router.get("/fast_deps")
async def fast_dependencies(
    _: int = Depends(dep_without_delays),
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


dag_size, dep_with_delays = generate_dag(
    make_depends, glbls, *DAG_SHAPE, sleep=DELAY
)
print("/slow_deps dag size: ", dag_size)


@app.router.get("/slow_deps")
async def slow_dependencies(
    _: int = Depends(dep_with_delays),
) -> Response:
    """An endpoint with dependencies that simulate IO"""
    return Response()
