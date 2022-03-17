from typing import Any, Dict

from docs_src.tutorial.routing.tutorial_001 import app
from xpresso.testclient import TestClient


def test_routing() -> None:
    client = TestClient(app)

    resp = client.get("/mount/mount-again/items")
    assert resp.status_code == 200, resp.content


def test_openapi() -> None:
    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/mount/mount-again/items": {
                "get": {"responses": {"200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }}}
            }
        },
    }

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
