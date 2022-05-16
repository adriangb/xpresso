from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List

import anyio
import anyio.abc
import pytest
from di.container import Container
from di.dependant import Dependant
from di.executors import SyncExecutor
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


def test_bind_from_lifespan() -> None:
    class Foo:
        pass

    class Bar(Foo):
        pass

    @asynccontextmanager
    async def lifespan(app: App) -> AsyncIterator[None]:
        with app.dependency_overrides as overrides:
            overrides[Foo] = Bar
            yield

    async def endpoint(foo: Foo) -> None:
        assert isinstance(foo, Bar)

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


def test_custom_scope() -> None:
    """Users that set up containers outside of Xpresso
    should be able to use custom scopes
    """

    class Foo:
        counter: int = 0

        def __init__(self) -> None:
            Foo.counter += 1

    container = Container()
    dep = Dependant(Foo, scope="global")

    # outside of Xpresso system
    exec = SyncExecutor()
    solved = container.solve(dep, scopes=["global"])
    with container.enter_scope("global") as global_state:
        assert Foo.counter == 0
        container.execute_sync(solved, exec, state=global_state)
        assert Foo.counter == 1
        # Foo is cached in the "global" scope
        container.execute_sync(solved, exec, state=global_state)
        assert Foo.counter == 1

    # within Xpresso

    # TODO: Depends()'s static typing rejects "global"
    # and Dependant() is ignored if used instead (a bug?)
    # I think users should be able to use Dependant() here in place of Depends()
    # and Depends() should continue to enforce Xpresso specific scopes
    async def endpoint(foo: Annotated[Foo, Depends(scope="global")]) -> None:
        ...

    routes = [Path("/", get=endpoint)]
    with container.enter_scope("global") as global_state:
        app = App(
            routes, custom_dependency_scopes=["global"], container_state=global_state
        )
        client = TestClient(app)

        resp = client.get("/")
        assert resp.status_code == 200
        assert Foo.counter == 2

        # Foo is cached in the "global" scope
        resp = client.get("/")
        assert resp.status_code == 200
        assert Foo.counter == 2
