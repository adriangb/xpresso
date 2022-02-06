from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List

from di import BaseContainer
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Depends, Operation, Path
from xpresso.typing import Annotated


def test_router_route_dependencies() -> None:
    """Test mixing dependencies from routers, routes and endpoints"""

    class TrackingDep:
        o: object = None

        def __call__(self, o: Annotated[object, Depends(scope="app")]) -> None:
            self.o = o

    router_dep = TrackingDep()
    route_dep = TrackingDep()
    endpoint_dep = TrackingDep()

    async def endpoint(v: Annotated[None, Depends(endpoint_dep)]) -> Response:
        return Response()

    app = App(
        routes=[Path("/", get=Operation(endpoint, dependencies=[Depends(route_dep)]))],
        dependencies=[Depends(router_dep)],
    )

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert endpoint_dep.o is route_dep.o and route_dep.o is router_dep.o


def test_lifespan_dependencies() -> None:
    @dataclass
    class Test:
        foo: str = "foo"

    TestDep = Annotated[Test, Depends(scope="app")]

    @asynccontextmanager
    async def lifespan(t: TestDep) -> AsyncIterator[None]:
        t.foo = "bar"
        yield

    async def endpoint(t: TestDep) -> str:
        return t.foo

    app = App([Path("/", get=endpoint)], lifespan=lifespan)

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == "bar"


def test_inject_container() -> None:
    @asynccontextmanager
    async def lifespan(container: BaseContainer) -> AsyncIterator[None]:
        assert tuple(container.current_scopes) == ("app",)
        yield

    app = App([], lifespan=lifespan)

    with TestClient(app=app):
        pass


def test_inject_app() -> None:

    log: List[int] = []

    @asynccontextmanager
    async def lifespan(app: App) -> AsyncIterator[None]:
        log.append(id(app))
        yield

    async def endpoint(app: App) -> Response:
        assert log == [id(app)]
        return Response()

    app = App([Path("/", get=endpoint)], lifespan=lifespan)

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
