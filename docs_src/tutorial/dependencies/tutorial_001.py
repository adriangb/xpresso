from typing import Dict

import httpx

from xpresso import App, Path


async def echo_headers(client: httpx.AsyncClient) -> Dict[str, str]:
    resp = await client.get("https://httpbin.org/get")
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
