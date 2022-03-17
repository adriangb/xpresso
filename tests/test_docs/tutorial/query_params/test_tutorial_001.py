import json
from typing import Any, Dict

import pytest

from docs_src.tutorial.query_params.tutorial_001 import app
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
                            "description": "Successful Response",
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
                        "schema": {"title": "Limit", "type": "integer", "default": 2},
                        "name": "limit",
                        "in": "query",
                    },
                    {
                        "style": "form",
                        "explode": True,
                        "schema": {"title": "Skip", "type": "integer", "default": 0},
                        "name": "skip",
                        "in": "query",
                    },
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


def test_read_items():
    response = client.get("/items/", params={"skip": 1, "limit": 1})
    assert response.status_code == 200, response.content
    assert response.json() == json.load(
        open("docs_src/tutorial/query_params/tutorial_001_response_1.json")
    )


@pytest.mark.parametrize(
    "params",
    [
        {"skip": "0"},
        {"limit": "2"},
        {"skip": "0", "limit": "2"},
        {},
    ],
)
def test_read_items_defaults(params: Dict[str, str]):
    response = client.get("/items/", params=params)
    assert response.status_code == 200, response.content
    assert response.json() == json.load(
        open("docs_src/tutorial/query_params/tutorial_001_response_2.json")
    )
