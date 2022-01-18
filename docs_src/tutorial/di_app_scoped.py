from dataclasses import dataclass

from xpresso import App, Dependant, Path
from xpresso.typing import Annotated


@dataclass
class Config:
    host: str


async def root(
    # we will always get the same instance of Config
    config: Annotated[Config, Dependant(Config, scope="app")]
) -> str:
    return f"Hello from {config.host}!"


app = App(routes=[Path(path="/", get=root)])
