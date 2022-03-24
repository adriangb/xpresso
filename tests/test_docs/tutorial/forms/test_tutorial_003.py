from io import BytesIO
from typing import Any, Dict, List

import pytest

from docs_src.tutorial.forms.tutorial_003 import app
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
                        "description": "OK",
                        "content": {"application/json": {"schema": {"type": "string"}}},
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
                        "multipart/form-data": {
                            "schema": {
                                "required": ["name", "files"],
                                "type": "object",
                                "properties": {
                                    "name": {"title": "Name", "type": "string"},
                                    "files": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "binary"},
                                    },
                                },
                            },
                            "encoding": {
                                "name": {"style": "form", "explode": True},
                                "files": {},
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
    "files, result",
    [
        (("tag1", "tag2"), "John uploaded tag1, tag2"),
        ((), "John uploaded "),
    ],
)
def test_upload(files: List[str], result: str):
    class TruthyList(List[Any]):  # forces a multipart request even with no files
        def __bool__(self) -> bool:
            return True

    response = client.post(
        "/form",
        data=[("name", "John")],
        files=TruthyList(
            [("files", ("file.txt", BytesIO(f.encode()), "text/plain")) for f in files]
        ),
    )
    assert response.status_code == 200, response.content
    assert response.json() == result
