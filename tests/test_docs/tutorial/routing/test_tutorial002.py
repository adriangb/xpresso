from typing import Any, Dict

from docs_src.tutorial.routing.tutorial_002 import app
from xpresso.testclient import TestClient


def test_openapi() -> None:
    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/v1/items": {
                "get": {
                    "responses": {"404": {"description": "Item not found"}},
                    "tags": ["v1", "items", "read"],
                    "summary": "List all items",
                    "description": "The **items** operation",
                    "deprecated": True,
                },
                "post": {
                    "responses": {
                        "404": {"description": "Item not found"},
                        "204": {"description": "Success"},
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
                    "tags": ["v1", "items", "write"],
                    "description": "Documentation from docstrings!\n    You can use any valid markdown, for example lists:\n\n    - Point 1\n    - Point 2\n    ",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"}
                            }
                        },
                        "required": True,
                    },
                    "servers": [
                        {"url": "https://us-east-1.example.com"},
                        {"url": "http://127.0.0.1:8000"},
                    ],
                },
                "servers": [{"url": "http://127.0.0.1:8000"}],
            }
        },
        "components": {
            "schemas": {
                "Item": {
                    "title": "Item",
                    "required": ["name", "price"],
                    "type": "object",
                    "properties": {
                        "name": {"title": "Name", "type": "string"},
                        "price": {"title": "Price", "type": "number"},
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
