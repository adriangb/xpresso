from contextlib import ExitStack

import httpx

from docs_src.tutorial.dependencies.tutorial_003 import HttpBinConfigModel, app
from xpresso import Depends
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

    with ExitStack() as stack:
        stack.enter_context(
            app.container.register_by_type(
                Depends(lambda: HttpBinConfigModel(url=test_url)),
                HttpBinConfigModel,
            )
        )
        stack.enter_context(
            app.container.register_by_type(
                Depends(get_client),
                httpx.AsyncClient,
            )
        )
        client = TestClient(app)
        response = client.get("/echo/url")
        assert response.status_code == 200, response.content
        assert response.json() == test_url + "/get"
