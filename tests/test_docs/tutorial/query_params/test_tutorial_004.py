from typing import Any, Dict, Iterable, Tuple

import pytest

from docs_src.tutorial.query_params.tutorial_004 import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/items/": {
            "get": {
                "responses": {
                    "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
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
                        "style": "form",
                        "explode": True,
                        "schema": {
                            "title": "Prefix",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "name": "prefix",
                        "in": "query",
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
                        "items": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
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


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.content
    assert response.json() == openapi_schema


@pytest.mark.parametrize(
    "params,json_response",
    [
        ([], [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]),
        ([("prefix", "B")], [{"item_name": "Bar"}, {"item_name": "Baz"}]),
        ([("prefix", "B"), ("prefix", "Baz")], [{"item_name": "Baz"}]),
        ([("prefix", "B"), ("prefix", "F")], []),
    ],
)
def test_read_item(params: Iterable[Tuple[str, str]], json_response: Dict[str, Any]):
    response = client.get("/items/", params=params)
    assert response.status_code == 200, response.content
    assert response.json() == json_response
