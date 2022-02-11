import httpx

from docs_src.tutorial.dependencies.tutorial_001 import app
from xpresso.testclient import TestClient


def test_client_injection():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://httpbin.org/get"
        return httpx.Response(200, json={"url": "https://httpbin.org/get"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    with app.dependency_overrides:
        app.dependency_overrides[httpx.AsyncClient] = lambda: http_client

        client = TestClient(app)
        response = client.get("/echo/url")
        assert response.status_code == 200, response.content
        assert response.json() == "https://httpbin.org/get"
