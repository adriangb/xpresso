from typing import Any, Dict

from docs_src.advanced.responses.tutorial_004 import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/items/": {
            "post": {
                "responses": {
                    "204": {
                        "description": "Successful Response",
                        "content": {"application/json": {}},
                    }
                }
            }
        }
    },
}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_create_image():
    response = client.post("/items/", json={"id": "foo", "value": "bar"})
    assert response.status_code == 204, response.text
