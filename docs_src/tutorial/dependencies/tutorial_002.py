import httpx

from xpresso import App, Depends, Path
from xpresso.typing import Annotated


def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="https://httpbin.org")


HttpbinClient = Annotated[httpx.AsyncClient, Depends(get_client)]


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
