from typing import Dict

import httpx

from xpresso import App, Dependant, Path
from xpresso.typing import Annotated


def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="https://httpbin.org")


HttpbinClient = Annotated[httpx.AsyncClient, Dependant(get_client)]


async def echo_headers(client: HttpbinClient) -> Dict[str, str]:
    resp = await client.get("/get")
    resp.raise_for_status()  # or some other error handling
    return resp.json()["headers"]


app = App(
    routes=[
        Path(
            "/echo/headers",
            get=echo_headers,
        )
    ]
)
