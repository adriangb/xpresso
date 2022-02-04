from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from xpresso import App, Path, Router
from xpresso.routing.mount import Mount


class Logger(List[str]):
    pass


@asynccontextmanager
async def app_lifespan(logger: Logger) -> AsyncIterator[None]:
    logger.append("App lifespan")
    yield


@asynccontextmanager
async def router_lifespan(logger: Logger) -> AsyncIterator[None]:
    logger.append("Router lifespan")
    yield


async def get_logs(logger: Logger) -> List[str]:
    return logger


app = App(
    routes=[
        Mount(
            "",
            app=Router(
                routes=[
                    Path(
                        "/logs",
                        get=get_logs,
                    )
                ],
                lifespan=router_lifespan,
            ),
        )
    ],
    lifespan=app_lifespan,
)
