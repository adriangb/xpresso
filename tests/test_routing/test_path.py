from typing import Any, Dict

import pytest

from xpresso import App, FromPath, Path, Request
from xpresso.testclient import TestClient


@pytest.mark.parametrize("path", ["foo", "", "foo/"])
def test_path_item_invalid_path(path: str) -> None:
    with pytest.raises(ValueError, match="must start with '/'"):
        Path("test")
    with pytest.raises(ValueError, match="must start with '/'"):
        Path("")


@pytest.mark.parametrize(
    "method",
    [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "connect",
        "options",
        "trace",
    ],
)
def test_methods(method: str) -> None:
    async def endpoint(request: Request) -> None:
        assert request.method.lower() == method

    app = App([Path("/", **{method: endpoint})])  # type: ignore[arg-type]
    client = TestClient(app)
    resp = client.request(method=method, url="/")
    assert resp.status_code == 200, resp.content


def test_unsupported_method() -> None:
    async def endpoint() -> None:
        ...

    app = App([Path("/", get=endpoint)])
    client = TestClient(app)
    resp = client.post("/")
    assert resp.status_code == 405, resp.content


@pytest.mark.parametrize("path", ["foo", "https://foo.com/bar", "foo/bar/baz/"])
def test_catchall_path(path: str) -> None:
    async def endpoint(catchall: FromPath[str]) -> str:
        return catchall

    app = App([Path("/{catchall:path}", get=endpoint)])
    client = TestClient(app)

    resp = client.get(f"/{path}")
    assert resp.status_code == 200, resp.content
    assert resp.json() == path


def test_path_parameter_converter_is_removed_from_openapi():
    async def endpoint(catchall: FromPath[str]) -> str:
        return catchall

    app = App([Path("/api/{catchall:path}", get=endpoint)])
    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            # We MUST remove the {:converter} part from here
            # since that is not part of the OpenAPI spec
            "/api/{catchall}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {"schema": {"type": "string"}}
                            },
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "parameters": [
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Catchall", "type": "string"},
                            "name": "catchall",
                            "in": "path",
                        }
                    ],
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
