
from typing import Any, Callable, Dict

from docs_src.advanced.responses.tutorial_001 import app
from xpresso.testclient import TestClient

client = TestClient(app)


def test_openapi_schema(compare_or_create_expected_openapi: Callable[[Dict[str, Any]], None]):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    compare_or_create_expected_openapi(response.json())
