from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List

import anyio
import anyio.abc
import pytest
from di.container import Container
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Depends, Operation, Path, WebSocket, WebSocketRoute
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


def test_lifespan_dependencies_are_re_used_in_connection_scope() -> None:
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


@pytest.mark.parametrize("use_lifespan", [True, False])
def test_app_scope_dependency_is_initialized_in_lifespan_http_endpoint(
    use_lifespan: bool,
) -> None:
    async def dep() -> AsyncIterator[None]:
        taskinfo = anyio.get_current_task()
        yield
        # make sure we are in the same task'
        # https://github.com/adriangb/xpresso/pull/57/files#r801949751
        assert taskinfo.id == anyio.get_current_task().id

    Dep = Annotated[None, Depends(dep, scope="app")]

    @asynccontextmanager
    async def lifespan(t: Dep) -> AsyncIterator[None]:
        taskinfo = anyio.get_current_task()
        yield
        assert taskinfo.id == anyio.get_current_task().id

    async def endpoint(t: Dep) -> None:
        ...

    app = App([Path("/", get=endpoint)], lifespan=lifespan if use_lifespan else None)

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200, resp.content


@pytest.mark.parametrize("use_lifespan", [True, False])
def test_app_scope_dependency_is_initialized_in_lifespan_websocket_endpoint(
    use_lifespan: bool,
) -> None:
    async def dep() -> AsyncIterator[None]:
        taskinfo = anyio.get_current_task()
        yield
        # make sure we are in the same task'
        # https://github.com/adriangb/xpresso/pull/57/files#r801949751
        assert taskinfo.id == anyio.get_current_task().id

    Dep = Annotated[None, Depends(dep, scope="app")]

    @asynccontextmanager
    async def lifespan(t: Dep) -> AsyncIterator[None]:
        taskinfo = anyio.get_current_task()
        yield
        assert taskinfo.id == anyio.get_current_task().id

    async def endpoint(t: Dep, ws: WebSocket) -> None:
        await ws.accept()
        await ws.send_text("Hello")
        await ws.close()

    app = App(
        [WebSocketRoute("/", endpoint=endpoint)],
        lifespan=lifespan if use_lifespan else None,
    )

    with TestClient(app=app) as client:
        with client.websocket_connect("/") as ws:
            resp = ws.receive_text()
    assert resp == "Hello"


def test_inject_container() -> None:
    @asynccontextmanager
    async def lifespan(container: Container) -> AsyncIterator[None]:
        assert container is app.container
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


def test_default_scope_for_autowired_deps() -> None:
    """Child dependencies of an "endpoint" scoped dep (often the endpoint itself)
    should have a "connection" scope so that they are compatible with the default scope of Depends().
    """

    class Dep:
        pass

    async def endpoint(d1: Dep, d2: Annotated[Dep, Depends()]) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    with TestClient(app=app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
