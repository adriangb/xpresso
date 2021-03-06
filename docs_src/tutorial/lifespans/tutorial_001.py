from contextlib import asynccontextmanager
from typing import AsyncIterator

from pydantic import BaseModel

from xpresso import App, Path


class AppState(BaseModel):
    started: bool = False


@asynccontextmanager
async def lifespan(state: AppState) -> AsyncIterator[None]:
    state.started = True
    yield


class AppHealth(BaseModel):
    running: bool


async def healthcheck(state: AppState) -> AppHealth:
    return AppHealth(running=state.started)


app = App(
    lifespan=lifespan, routes=[Path("/health", get=healthcheck)]
)
