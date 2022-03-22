from typing import Any, Dict

import pytest

from docs_src.tutorial.header_params.tutorial_001 import app
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
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                }
                            }
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
                        "style": "simple",
                        "explode": False,
                        "schema": {
                            "title": "Accept Language",
                            "type": "string",
                            "nullable": True,
                        },
                        "name": "accept_language",
                        "in": "header",
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
    "headers,json_response",
    [
        ({"Accept-Language": "en"}, {"Accept-Language": "en"}),
        ({"Accept-Language": ""}, {"Accept-Language": ""}),
        ({}, {"Accept-Language": None}),
    ],
)
def test_get_items(headers: Dict[str, Any], json_response: Dict[str, Any]):
    response = client.get("/items/", headers=headers)
    assert response.status_code == 200, response.content
    assert response.json() == json_response
