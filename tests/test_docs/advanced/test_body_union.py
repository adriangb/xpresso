from typing import Any, Dict

from docs_src.advanced.body_union import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/items/": {
            "post": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": {"type": "number"},
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
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Item"}
                        },
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "required": ["name", "price"],
                                "type": "object",
                                "properties": {
                                    "name": {"title": "Name", "type": "string"},
                                    "price": {"title": "Price", "type": "number"},
                                    "tax": {
                                        "title": "Tax",
                                        "type": "number",
                                        "nullable": True,
                                    },
                                },
                            },
                            "encoding": {
                                "name": {"style": "form", "explode": True},
                                "price": {"style": "form", "explode": True},
                                "tax": {"style": "form", "explode": True},
                            },
                        },
                    },
                    "required": True,
                },
            }
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
                    "tax": {"title": "Tax", "type": "number"},
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


def test_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == openapi_schema


def test_post_form():
    response = client.post("/items/", data={"name": "hammer", "price": 1.0})
    assert response.status_code == 200
    assert response.json() == {"hammer": 1.0}


def test_post_json():
    response = client.post("/items/", json={"name": "hammer", "price": 1.0})
    assert response.status_code == 200
    assert response.json() == {"hammer": 1.0}
