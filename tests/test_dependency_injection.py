from contextlib import asynccontextmanager
from typing import AsyncIterator

from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Dependant, Operation, Path
from xpresso.typing import Annotated


def test_router_route_dependencies() -> None:
    """Test mixing dependencies from routers, routes and endpoints"""

    class TrackingDep:
        o: object = None

        def __call__(self, o: Annotated[object, Dependant(scope="app")]) -> None:
            self.o = o

    router_dep = TrackingDep()
    route_dep = TrackingDep()
    endpoint_dep = TrackingDep()

    async def endpoint(v: Annotated[None, Dependant(endpoint_dep)]) -> Response:
        return Response()

    app = App(
        routes=[
            Path("/", get=Operation(endpoint, dependencies=[Dependant(route_dep)]))
        ],
        dependencies=[Dependant(router_dep)],
    )

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert endpoint_dep.o is route_dep.o and route_dep.o is router_dep.o


def test_lifespan_dependencies() -> None:
    class Test:
        ...

    @asynccontextmanager
    async def lifespan(
        t: Annotated[Test, Dependant(scope="app")]
    ) -> AsyncIterator[None]:
        app.state.t = t  # type: ignore[has-type]
        yield

    async def endpoint(t: Annotated[Test, Dependant(scope="app")]) -> Response:
        assert app.state.t is t  # type: ignore[has-type]
        return Response()

    app = App([Path("/", get=endpoint)], lifespan=lifespan)

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
