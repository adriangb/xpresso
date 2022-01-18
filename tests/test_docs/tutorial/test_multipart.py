from typing import Any, Dict, Iterable, List, Tuple

import pytest

from docs_src.tutorial.multipart import app
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
                                "schema": {
                                    "$ref": "#/components/schemas/UserUploadMetadata"
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
                        "multipart/form-data": {
                            "schema": {
                                "required": ["name", "tags", "files"],
                                "type": "object",
                                "properties": {
                                    "name": {"title": "Name", "type": "string"},
                                    "tags": {
                                        "title": "Tags",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "files": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "binary"},
                                    },
                                },
                            },
                            "encoding": {
                                "name": {"style": "form", "explode": True},
                                "tags": {"style": "form", "explode": True},
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
            "UserUploadMetadata": {
                "title": "UserUploadMetadata",
                "required": ["name", "tags", "nbytes"],
                "type": "object",
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "tags": {
                        "title": "Tags",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "nbytes": {"title": "Nbytes", "type": "integer"},
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


@pytest.mark.parametrize(
    "file_data,nbytes",
    [
        ((b"123", "456"), 6),
        ((), 0),
    ],
)
@pytest.mark.parametrize("tags", [["tag1", "tag2"], []])
def test_upload(file_data: Iterable[bytes], nbytes: int, tags: List[str]):
    class TruthyEmptyList(List[Any]):
        def __bool__(self) -> bool:
            return True

    files = TruthyEmptyList([("files", ("file.txt", data)) for data in file_data])
    data: List[Tuple[str, str]] = [
        ("name", "John Snow"),
    ]
    for tag in tags:
        data.append(("tags", tag))
    response = client.post("/form", files=files, data=data)
    assert response.status_code == 200, response.content
    assert response.json() == {
        "name": "John Snow",
        "tags": tags,
        "nbytes": nbytes,
    }
