import json
from typing import Any, Dict

from docs_src.tutorial.query_params.tutorial_006 import app
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
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Filter"}
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
                        "required": True,
                        "style": "deepObject",
                        "explode": True,
                        "schema": {
                            "$ref": "#/components/schemas/Filter",
                            "nullable": True,
                        },
                        "name": "filter",
                        "in": "query",
                    }
                ],
            }
        }
    },
    "components": {
        "schemas": {
            "Filter": {
                "title": "Filter",
                "required": ["prefix", "limit"],
                "type": "object",
                "properties": {
                    "prefix": {"title": "Prefix", "type": "string"},
                    "limit": {"title": "Limit", "type": "integer"},
                    "skip": {"title": "Skip", "type": "integer", "default": 0},
                },
            },
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
    response = client.get(
        "/items/", params=[("filter[prefix]", "Ba"), ("filter[limit]", "1")]
    )
    assert response.status_code == 200, response.content
    assert response.json() == json.load(
        open("docs_src/tutorial/query_params/tutorial_006_response_1.json")
    )
