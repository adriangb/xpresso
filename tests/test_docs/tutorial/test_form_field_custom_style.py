from typing import Any, Dict, Mapping

import pytest

from docs_src.tutorial.form_field_custom_style import app
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/echo-tags": {
            "post": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "title": "Response",
                                    "type": "array",
                                    "items": {"type": "string"},
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
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "required": ["tags"],
                                "type": "object",
                                "properties": {
                                    "tags": {
                                        "title": "Tags",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                },
                            },
                            "encoding": {
                                "tags": {"style": "spaceDelimited", "explode": False}
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
    "data,json_response,status_code",
    [
        ({"tags": "tag1 tag2"}, ["tag1", "tag2"], 200),
        ({"tags": "tag1"}, ["tag1"], 200),
        ({}, [], 200),
    ],
)
def test_echo_tags(
    data: Mapping[str, str], json_response: Dict[str, Any], status_code: int
) -> None:
    resp = client.post(
        "/echo-tags",
        data=data,
        headers={"content-type": "application/x-www-form-urlencoded"},
    )  # include header for empty dict
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response
