import httpx

from docs_src.tutorial.dependencies.tutorial_001 import app
from xpresso import Dependant
from xpresso.testclient import TestClient


def test_client_injection():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://httpbin.org/get"
        return httpx.Response(200, json={"url": "https://httpbin.org/get"})

    with app.container.register_by_type(
        Dependant(lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))),
        httpx.AsyncClient,
    ):
        with TestClient(app) as client:
            response = client.get("/echo/url")
            assert response.status_code == 200, response.content
            assert response.json() == "https://httpbin.org/get"
