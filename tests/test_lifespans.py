from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from xpresso import App, Router
from xpresso.routing.mount import Mount
from xpresso.testclient import TestClient


def test_lifespan_mounted_app() -> None:
    class Counter(List[int]):
        pass

    @asynccontextmanager
    async def lifespan(counter: Counter) -> AsyncIterator[None]:
        counter.append(1)
        yield

    counter = Counter()

    inner_app = App(lifespan=lifespan)
    inner_app.dependency_overrides[Counter] = lambda: counter

    app = App(
        routes=[
            Mount("/mounted-app", app=inner_app),
            Mount("/mounted-router", app=Router([], lifespan=lifespan)),
        ],
        lifespan=lifespan,
    )

    app.dependency_overrides[Counter] = lambda: counter

    with TestClient(app):
        pass

    assert counter == [1, 1, 1]
