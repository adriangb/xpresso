
from typing import Any, Dict

from docs_src.advanced.responses.tutorial_002 import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/items/{item_id}": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"}
                            },
                            "image/png": {
                                "schema": {
                                    "title": "Response",
                                    "type": "string",
                                    "format": "binary",
                                }
                            },
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
                        "style": "form",
                        "explode": True,
                        "schema": {"title": "Img", "type": "boolean", "nullable": True},
                        "name": "img",
                        "in": "query",
                    },
                    {
                        "required": True,
                        "style": "simple",
                        "explode": False,
                        "schema": {"title": "Item Id", "type": "string"},
                        "name": "item_id",
                        "in": "path",
                    },
                ],
            }
        }
    },
    "components": {
        "schemas": {
            "Item": {
                "title": "Item",
                "required": ["id", "value"],
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "string"},
                    "value": {"title": "Value", "type": "string"},
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
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema
