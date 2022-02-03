from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from xpresso import App, Dependant, Path, Router
from xpresso.routing.mount import Mount
from xpresso.typing import Annotated


class Logger(List[str]):
    pass


LoggerDep = Annotated[Logger, Dependant(scope="app")]


@asynccontextmanager
async def app_lifespan(
    logger: LoggerDep,
) -> AsyncGenerator[None, None]:
    logger.append("App lifespan")
    yield


@asynccontextmanager
async def router_lifespan(
    logger: LoggerDep,
) -> AsyncGenerator[None, None]:
    logger.append("Router lifespan")
    yield


async def get_logs(logger: LoggerDep) -> List[str]:
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
