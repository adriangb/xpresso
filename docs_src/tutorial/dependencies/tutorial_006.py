from typing import AsyncGenerator

import httpx
from pydantic import BaseSettings

from xpresso import App, Dependant, Path
from xpresso.typing import Annotated


class HttpBinConfigModel(BaseSettings):
    url: str = "https://httpbin.org"

    class Config(BaseSettings.Config):
        env_prefix = "HTTPBIN_"


HttpBinConfig = Annotated[
    HttpBinConfigModel, Dependant(lambda: HttpBinConfigModel(), scope="app")
]


async def get_client(config: HttpBinConfig) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=config.url) as client:
        yield client


HttpbinClient = Annotated[httpx.AsyncClient, Dependant(get_client, scope="app")]


async def echo_url(client: HttpbinClient) -> str:
    resp = await client.get("/get")
    resp.raise_for_status()  # or some other error handling
    return resp.json()["url"]


app = App(
    routes=[
        Path(
            "/echo/url",
            get=echo_url,
        )
    ]
)
