from dataclasses import dataclass

from di.dependent import Marker

from xpresso import App, Depends, Path
from xpresso.dependencies import Injectable
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


def test_override_with_marker() -> None:
    def dep() -> int:
        ...

    async def endpoint(v: Annotated[int, Depends(dep)]) -> int:
        return v

    app = App([Path("/", get=endpoint)])

    app.dependency_overrides[dep] = lambda: 2

    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 2


def test_override_with_non_xpresso_marker() -> None:
    def dep() -> int:
        ...

    async def endpoint(v: Annotated[int, Marker(dep, scope="endpoint")]) -> int:
        return v

    app = App([Path("/", get=endpoint)])

    app.dependency_overrides[dep] = lambda: 2

    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 2


def test_override_match_by_annotation() -> None:
    @dataclass
    class Foo:
        bar: str = "bar"

    async def endpoint(foo: Foo) -> str:
        return foo.bar

    app = App([Path("/", get=endpoint)])

    app.dependency_overrides[Foo] = lambda: Foo(bar="baz")

    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "baz"


def test_override_injectable_cls() -> None:
    @dataclass
    class Foo(Injectable):
        bar: str = "bar"

    async def endpoint(foo: Foo) -> str:
        return foo.bar

    app = App([Path("/", get=endpoint)])

    app.dependency_overrides[Foo] = lambda: Foo(bar="baz")

    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "baz"
