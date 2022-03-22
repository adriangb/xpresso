from typing import Any, Dict

import msgpack  # type: ignore[import]
from pydantic import BaseModel

from xpresso import App, Path
from xpresso.testclient import TestClient

from .functions import FromMsgPack


class Item(BaseModel):
    foo: str
    bar: int


async def echo_item(item: FromMsgPack[Item]) -> Item:
    return item


app = App(
    routes=[
        Path(
            "/echo-item",
            put=echo_item,
        )
    ]
)

client = TestClient(app)


def test_echo_item() -> None:
    payload = {"foo": "abc", "bar": 123}
    data: bytes = msgpack.packb(payload)  # type: ignore[assignment]

    resp = client.put("/echo-item", data=data)

    assert resp.status_code == 200, resp.content
    assert resp.json() == payload


def test_openapi_schema() -> None:
    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/echo-item": {
                "put": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Item"
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
                            "application/x-msgpack": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary",
                                }
                            }
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
                    "required": ["foo", "bar"],
                    "type": "object",
                    "properties": {
                        "foo": {"title": "Foo", "type": "string"},
                        "bar": {"title": "Bar", "type": "integer"},
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
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "integer"},
                                ]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {
                            "title": "Error Type",
                            "type": "string",
                        },
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/ValidationError"
                            },
                        }
                    },
                },
            }
        },
    }

    resp = client.get("/openapi.json")

    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


if __name__ == "__main__":
    test_echo_item()
    test_openapi_schema()
