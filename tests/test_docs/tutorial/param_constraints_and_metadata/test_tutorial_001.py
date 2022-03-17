from typing import Any, Dict

from docs_src.tutorial.param_constraints_and_metadata.tutorial_001 import app
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
                        "description": "Maximum number of items to return",
                        "required": True,
                        "style": "form",
                        "explode": True,
                        "schema": {
                            "title": "Limit",
                            "exclusiveMinimum": 0.0,
                            "type": "integer",
                            "description": "Maximum number of items to return",
                        },
                        "name": "limit",
                        "in": "query",
                    },
                    {
                        "description": "Count of items to skip starting from the 0th item",
                        "required": True,
                        "style": "form",
                        "explode": True,
                        "schema": {
                            "title": "Skip",
                            "exclusiveMinimum": 0.0,
                            "type": "integer",
                        },
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
