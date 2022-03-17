from typing import Any, Dict

from xpresso import App, Operation, Path
from xpresso.testclient import TestClient


def test_default_response_spec_merge_type() -> None:
    async def endpoint() -> str:
        return ""

    app = App(
        routes=[
            Path(
                "/",
                post=Operation(
                    endpoint,
                    default_response_status_code=201,
                    default_response_description="Created",
                ),
            )
        ]
    )

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "201": {
                            "description": "Created",
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
    }

    client = TestClient(app)

    resp = client.post("/")
    assert resp.status_code == 201, resp.content

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
