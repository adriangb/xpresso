from typing import Any, Dict, List

from msgspec import Struct

from xpresso import App, Path
from xpresso.testclient import TestClient

from .functions import FromJson


class Item(Struct):
    foo: str
    bar: int


async def echo_item(items: FromJson[List[Item]]) -> int:
    return len(items)


app = App(
    routes=[
        Path(
            "/count-items",
            put=echo_item,
        )
    ]
)

client = TestClient(app)


def test_count_items() -> None:
    payload = [{"foo": "abc", "bar": 123}]

    resp = client.put("/count-items", json=payload)

    assert resp.status_code == 200, resp.content
    assert resp.json() == 1


def test_openapi_schema() -> None:
    expected_openapi: Dict[str, Any] = {
        "info": {"title": "API", "version": "0.1.0"},
        "openapi": "3.0.3",
        "paths": {
            "/count-items": {
                "put": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "items": {
                                        "$ref": "#/components/schemas/Item"
                                    },
                                    "type": "array",
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "integer"}
                                }
                            },
                            "description": "OK",
                        },
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
                }
            }
        },
        "components": {
            "schemas": {
                "HTTPValidationError": {
                    "properties": {
                        "detail": {
                            "items": {
                                "$ref": "#/components/schemas/ValidationError"
                            },
                            "title": "Detail",
                            "type": "array",
                        }
                    },
                    "title": "HTTPValidationError",
                    "type": "object",
                },
                "Item": {
                    "properties": {
                        "bar": {"type": "integer"},
                        "foo": {"type": "string"},
                    },
                    "required": ["foo", "bar"],
                    "title": "Item",
                    "type": "object",
                },
                "ValidationError": {
                    "properties": {
                        "loc": {
                            "items": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "integer"},
                                ]
                            },
                            "title": "Location",
                            "type": "array",
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {
                            "title": "Error Type",
                            "type": "string",
                        },
                    },
                    "required": ["loc", "msg", "type"],
                    "title": "ValidationError",
                    "type": "object",
                },
            }
        },
    }

    resp = client.get("/openapi.json")

    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


if __name__ == "__main__":
    test_count_items()
    test_openapi_schema()
