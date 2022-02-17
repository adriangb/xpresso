from typing import Any, Dict

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
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response", "type": "string"}
                            }
                        },
                    }
                }
            }
        }
    },
    "servers": [{"url": "/v1/api"}],
}


def test_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == openapi_schema


def test_main():
    response = client.get("/app")
    assert response.status_code == 200
    assert response.json() == "Hello from https://example.com/v1/api/app"
