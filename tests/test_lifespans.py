from contextlib import asynccontextmanager
from typing import AsyncIterator, List

import pytest

from xpresso import App, Dependant
from xpresso.routing.mount import Mount
from xpresso.testclient import TestClient


def test_lifespan_mounted_app() -> None:
    class Counter(List[int]):
        pass

    @asynccontextmanager
    async def lifespan(counter: Counter) -> AsyncIterator[None]:
        counter.append(1)
        yield

    app = App(
        routes=[Mount("/mounted-app", app=App(lifespan=lifespan))], lifespan=lifespan
    )

    counter = Counter()
    app.container.register_by_type(Dependant(lambda: counter, scope="app"), Counter)

    with TestClient(app):
        pass

    assert counter == [1, 1]


def test_lifespan_raises_exception_startup() -> None:
    class SomeExc(Exception):
        pass

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        raise SomeExc
        yield  # type: ignore[unreachable]

    app = App(lifespan=lifespan)

    client = TestClient(app)

    with pytest.raises(SomeExc):
        client.__enter__()


def test_lifespan_raises_exception_shutdown() -> None:
    class SomeExc(Exception):
        pass

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        yield
        raise SomeExc

    app = App(lifespan=lifespan)

    client = TestClient(app)

    client = client.__enter__()
    with pytest.raises(SomeExc):
        client.__exit__(None, None, None)
