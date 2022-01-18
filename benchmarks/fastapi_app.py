from fastapi import Depends
from fastapi import FastAPI as App
from starlette.responses import Response

from benchmarks.utils import generate_dag

app = App()


def make_depends(type_: str, provider: str) -> str:
    return f"{type_} = Depends({provider})"


glbls = {"Depends": Depends}


@app.router.get("/simple")
async def simple() -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


dep_without_delays = generate_dag(make_depends, glbls, 3, 2, 2, sleep=(0, 0))


@app.router.get("/fast_deps")
async def fast_dependencies(
    _: int = Depends(dep_without_delays),
) -> Response:
    """An endpoint with dependencies that execute instantly"""
    return Response()


# Establishing an asyncpg -> PostgreSQL connection takes ~75ms
# Running query takes about 1ms
# Hitting okta.com w/ httpx takes ~100ms
# So we'll take a range of 1ms to 100ms as delays for async dependencies
# And then make a medium sized DAG (3 levels, 2 deps per level, so 6 deps total)
dep_with_delays = generate_dag(make_depends, glbls, 3, 2, 2, sleep=(1e-3, 1e-1))


@app.router.get("/slow_deps")
async def slow_dependencies(
    _: int = Depends(dep_with_delays),
) -> Response:
    """An endpoint with dependencies that simulate IO"""
    return Response()
