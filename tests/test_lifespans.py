from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from xpresso import App, Depends, Router
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
    inner_app.container.register_by_type(Depends(lambda: counter, scope="app"), Counter)

    app = App(
        routes=[
            Mount("/mounted-app", app=inner_app),
            Mount("/mounted-router", app=Router([], lifespan=lifespan)),
        ],
        lifespan=lifespan,
    )

    app.container.register_by_type(Depends(lambda: counter, scope="app"), Counter)

    with TestClient(app):
        pass

    assert counter == [1, 1, 1]
