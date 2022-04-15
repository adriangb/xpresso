from typing import Any, Dict

from docs_src.tutorial.routing.tutorial_002 import app
from xpresso.testclient import TestClient


def test_openapi() -> None:
    expected_openapi: Dict[str, Any] = {
        "components": {
            "schemas": {
                "HTTPValidationError": {
                    "properties": {
                        "detail": {
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                            "title": "Detail",
                            "type": "array",
                        }
                    },
                    "title": "HTTPValidationError",
                    "type": "object",
                },
                "Item": {
                    "properties": {
                        "name": {"title": "Name", "type": "string"},
                        "price": {"title": "Price", "type": "number"},
                    },
                    "required": ["name", "price"],
                    "title": "Item",
                    "type": "object",
                },
                "ValidationError": {
                    "properties": {
                        "loc": {
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                            "title": "Location",
                            "type": "array",
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                    "required": ["loc", "msg", "type"],
                    "title": "ValidationError",
                    "type": "object",
                },
            }
        },
        "info": {"title": "API", "version": "0.1.0"},
        "openapi": "3.0.3",
        "paths": {
            "/v1/items": {
                "get": {
                    "deprecated": True,
                    "description": "The **items** operation",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "additionalProperties": {
                                            "$ref": "#/components/schemas/Item"
                                        },
                                        "type": "object",
                                    }
                                }
                            },
                            "description": "OK",
                        },
                        "404": {"description": "Item not found"},
                    },
                    "summary": "List all items",
                    "tags": ["v1", "items", "read"],
                },
                "post": {
                    "description": "Documentation from docstrings!\nYou can use any valid markdown, for example lists:\n\n- Point 1\n- Point 2",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"}
                            }
                        },
                        "required": True,
                    },
                    "responses": {
                        "200": {
                            "content": {"application/json": {}},
                            "description": "OK",
                        },
                        "204": {"description": "Success"},
                        "404": {"description": "Item not found"},
                        "422": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                            "description": "Validation Error",
                        },
                    },
                    "servers": [
                        {"url": "https://us-east-1.example.com"},
                        {"url": "http://127.0.0.1:8000"},
                    ],
                    "tags": ["v1", "items", "write"],
                },
                "servers": [{"url": "http://127.0.0.1:8000"}],
            }
        },
    }

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
