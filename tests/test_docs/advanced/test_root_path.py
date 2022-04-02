from typing import Any, Callable, Dict

from docs_src.advanced.root_path import app
from xpresso.testclient import TestClient

client = TestClient(app, base_url="https://example.com")


def test_openapi(compare_or_create_expected_openapi: Callable[[Dict[str, Any]], None]):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    compare_or_create_expected_openapi(response.json())


def test_main():
    response = client.get("/app")
    assert response.status_code == 200
    assert response.json() == "Hello from https://example.com/v1/api/app"
