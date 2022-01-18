import httpx

from docs_src.tutorial.dependencies.tutorial_002 import app
from xpresso import Dependant
from xpresso.testclient import TestClient


def test_client_injection():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://httpbin.org/get"
        return httpx.Response(200, json={"headers": {"foo": "bar"}})

    with app.container.register_by_type(
        Dependant(
            lambda: httpx.AsyncClient(
                transport=httpx.MockTransport(handler), base_url="https://httpbin.org"
            )
        ),
        httpx.AsyncClient,
    ):
        with TestClient(app) as client:
            response = client.get("/echo/headers")
            assert response.status_code == 200, response.content
            assert response.json() == {"foo": "bar"}
