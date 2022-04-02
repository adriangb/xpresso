from typing import Any, Callable, Dict

from docs_src.advanced.root_path import app
from xpresso.testclient import TestClient

client = TestClient(app, base_url="https://example.com")

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/app": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"type": "string"}
                            }
                        },
                    }
                }
            }
        }
    },
    "servers": [{"url": "/v1/api"}],
}


def test_openapi(get_or_create_expected_openapi: Callable[[Dict[str, Any]], Dict[str, Any]]):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    received_openapi = response.json()
    expected_openapi = get_or_create_expected_openapi(response.json())
    assert expected_openapi == received_openapi


def test_main():
    response = client.get("/app")
    assert response.status_code == 200
    assert response.json() == "Hello from https://example.com/v1/api/app"
