from dataclasses import dataclass

from xpresso import App, Path
from xpresso.dependencies import Injectable, Singleton
from xpresso.testclient import TestClient


def test_singleton() -> None:
    class Foo:
        pass

    @dataclass
    class MyService(Singleton):
        foo: Foo

    async def endpoint(service: MyService) -> int:
        return id(service)

    app = App(routes=[Path("/", get=endpoint)])

    with TestClient(app) as client:
        resp1 = client.get("/")
        assert resp1.status_code == 200, resp1.content
        resp2 = client.get("/")
        assert resp2.status_code == 200, resp2.content
        assert resp1.json() == resp2.json()


def test_injectable() -> None:
    class Foo:
        pass

    @dataclass
    class MyService(Injectable):
        foo: Foo

    async def endpoint(service: MyService) -> int:
        return id(service)

    app = App(routes=[Path("/", get=endpoint)])

    with TestClient(app) as client:
        resp1 = client.get("/")
        assert resp1.status_code == 200, resp1.content
        resp2 = client.get("/")
        assert resp2.status_code == 200, resp2.content
        assert resp1.json() != resp2.json()
