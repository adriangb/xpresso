from typing import Any, Dict

from xpresso import App, Operation, Path
from xpresso.testclient import TestClient


def test_include_in_schema() -> None:
    async def endpoint() -> None:
        ...

    app = App([Path("/", get=Operation(endpoint, include_in_schema=False))])

    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {"/": {}},
    }

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
