from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from pydantic import BaseModel

from xpresso import App, Dependant, Path
from xpresso.typing import Annotated


class AppHealth(BaseModel):
    app_id: Optional[int] = None


HealthState = Annotated[AppHealth, Dependant(scope="app")]


@asynccontextmanager
async def lifespan(
    app: App, health: HealthState
) -> AsyncGenerator[None, None]:
    health.app_id = id(app)  # this is just a trivial example
    yield


async def healthcheck(health: HealthState) -> AppHealth:
    return health


app = App(
    lifespan=lifespan, routes=[Path("/health", get=healthcheck)]
)
