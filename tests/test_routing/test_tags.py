from typing import Any, Dict

import pytest
from requests import Response  # type: ignore[import]

from xpresso import App, Operation, Path, Request
from xpresso.testclient import TestClient


async def get(request: Request) -> None:
    assert str(request.method.lower()) == "get"


async def post(request: Request) -> None:
    assert str(request.method.lower()) == "post"


async def put(request: Request) -> None:
    assert str(request.method.lower()) == "put"


async def delete(request: Request) -> None:
    assert str(request.method.lower()) == "delete"


async def head(request: Request) -> None:
    assert str(request.method.lower()) == "head"


tags_app = App(
    [
        Path(
            path="/",
            get=Operation(get, tags=["get"]),
            post=Operation(post, tags=["post"]),
            put=Operation(put, tags=["put"]),
            delete=Operation(delete, tags=["delete"]),
            head=Operation(head, tags=["head"]),
        ),
    ]
)

tags_client = TestClient(tags_app)


@pytest.mark.parametrize(
    "method",
    [
        "get",
        "post",
        "put",
        "head",
        "delete",
    ],
)
def test_tags(method: str) -> None:
    resp: Response = getattr(tags_client, method)("/")
    assert resp.status_code == 200, resp.content


def test_tags_openapi() -> None:
    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {}},
                        }
                    },
                    "tags": ["get"],
                },
                "put": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {}},
                        }
                    },
                    "tags": ["put"],
                },
                "post": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {}},
                        }
                    },
                    "tags": ["post"],
                },
                "delete": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {}},
                        }
                    },
                    "tags": ["delete"],
                },
                "head": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {"application/json": {}},
                        }
                    },
                    "tags": ["head"],
                },
            }
        },
    }

    resp = tags_client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
