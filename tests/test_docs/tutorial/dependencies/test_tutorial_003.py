import httpx

from docs_src.tutorial.dependencies.tutorial_003 import HttpBinConfigModel, app
from xpresso.testclient import TestClient


def test_client_config_injection():

    test_url = "https://example.com"

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == test_url + "/get"
        return httpx.Response(200, json={"url": test_url + "/get"})

    # This dependency becomes the provider for the client
    # It will get auto-wired with the config, so we can use it to assert that the config
    # Was succesfully injected
    def get_client(config: HttpBinConfigModel) -> httpx.AsyncClient:
        assert config.url == test_url
        return httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url=config.url
        )

    with app.dependency_overrides as overrides:
        overrides[HttpBinConfigModel] = lambda: HttpBinConfigModel(url=test_url)
        overrides[httpx.AsyncClient] = get_client
        client = TestClient(app)
        response = client.get("/echo/url")
        assert response.status_code == 200, response.content
        assert response.json() == test_url + "/get"
