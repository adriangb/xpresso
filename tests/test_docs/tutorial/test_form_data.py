from typing import Any, Dict, List, Tuple

import pytest

from docs_src.tutorial.form_data import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/form": {
            "post": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response", "type": "boolean"}
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
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "required": ["name", "tags", "json_data"],
                                "type": "object",
                                "properties": {
                                    "name": {"title": "Name", "type": "string"},
                                    "tags": {
                                        "title": "Tags",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "json_data": {
                                        "$ref": "#/components/schemas/JsonModel"
                                    },
                                },
                            },
                            "encoding": {
                                "name": {"style": "form", "explode": True},
                                "tags": {"style": "form", "explode": True},
                                "json_data": {"contentType": "application/json"},
                            },
                        }
                    },
                    "required": True,
                },
            }
        }
    },
    "components": {
        "schemas": {
            "JsonModel": {
                "title": "JsonModel",
                "required": ["foo"],
                "type": "object",
                "properties": {"foo": {"title": "Foo", "type": "string"}},
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

{
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/form": {
            "post": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response", "type": "boolean"}
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
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "required": ["name", "tags", "json_data"],
                                "type": "object",
                                "properties": {
                                    "name": {"title": "Name", "type": "string"},
                                    "tags": {
                                        "title": "Tags",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "json_data": {
                                        "$ref": "#/components/schemas/JsonModel"
                                    },
                                },
                            },
                            "encoding": {
                                "name": {"style": "form", "explode": True},
                                "tags": {"style": "form", "explode": True},
                                "json_data": {"style": "form", "explode": True},
                            },
                        }
                    },
                    "required": True,
                },
            }
        }
    },
    "components": {
        "schemas": {
            "JsonModel": {
                "title": "JsonModel",
                "required": ["foo"],
                "type": "object",
                "properties": {"foo": {"title": "Foo", "type": "string"}},
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


@pytest.mark.parametrize(
    "tags, json_data, result",
    [
        (("tag1", "tag2"), ('{"foo": "tag1"}'), True),
        (("tag1", "tag2"), ('{"foo": "tag3"}'), False),
        ((), ('{"foo": "tag1"}'), False),
    ],
)
def test_upload(tags: List[str], json_data: str, result: bool):
    data: List[Tuple[str, str]] = [("tags", tag) for tag in tags]
    data.append(("name", "John Snow"))
    data.append(("json_data", json_data))
    response = client.post("/form", data=data)
    assert response.status_code == 200, response.content
    assert response.json() == result
