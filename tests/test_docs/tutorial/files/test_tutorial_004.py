from typing import Any, Dict

import pytest

from docs_src.tutorial.files.tutorial_004 import app
from xpresso import status
from xpresso.testclient import TestClient

client = TestClient(app)

openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/count-bytes": {
            "put": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"type": "integer"}
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
                        "image/*": {"schema": {"type": "string", "format": "binary"}}
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
    "headers,status_code,expected_response_json",
    [
        ({"Content-Type": "image/png"}, 200, 3),
        (
            {"Content-Type": "text/plain"},
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            {
                "detail": [
                    {
                        "loc": ["headers", "content-type"],
                        "msg": "Media type text/plain is not supported",
                        "type": "value_error",
                    }
                ]
            },
        ),
    ],
)
def test_put_file(
    headers: Dict[str, str],
    status_code: int,
    expected_response_json: Any,
):
    response = client.put("/count-bytes", content=b"123", headers=headers)
    assert response.status_code == status_code
    assert response.json() == expected_response_json
