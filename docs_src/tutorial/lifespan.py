from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from xpresso import App, Dependant
from xpresso.typing import Annotated


@dataclass  # or maybe use Pydantic's BaseSettings
class Config:
    token: str = "foobarbaz"


ConfigDep = Annotated[Config, Dependant(scope="app")]


@asynccontextmanager
async def lifespan(config: ConfigDep) -> AsyncGenerator[None, None]:
    print(config.token)
    yield


app = App(lifespan=lifespan)
