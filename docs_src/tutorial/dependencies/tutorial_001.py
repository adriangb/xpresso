import httpx

from xpresso import App, Path


async def echo_url(client: httpx.AsyncClient) -> str:
    resp = await client.get("https://httpbin.org/get")
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
