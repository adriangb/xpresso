from typing import Any, Dict

from xpresso import App, FromPath, Path
from xpresso.testclient import TestClient


async def users_get(user_id: FromPath[int]) -> int:
    assert user_id == 123
    return 1


async def users_post(user_id: FromPath[int]) -> int:
    assert user_id == 123
    return 2


async def user_tags(user_id: FromPath[int]) -> int:
    assert user_id == 123
    return 3


users_path = Path(
    path="/users/{user_id}",
    get=users_get,
    post=users_post,
)
users_tags_path = Path(path="/users/{user_id}/tags", get=user_tags)
app = App([users_tags_path, users_path])

client = TestClient(app)


def test_routing() -> None:
    resp = client.get("/users/123")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 1

    resp = client.post("/users/123")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 2

    resp = client.get("/users/123/tags")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 3

    resp = client.get("/notusers")
    assert resp.status_code == 404, resp.content

    resp = client.get("/users/123/tags/more")
    assert resp.status_code == 404, resp.content


def test_openapi() -> None:
    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/users/{user_id}/tags": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"title": "Response", "type": "integer"}
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
                    "parameters": [
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "User Id", "type": "integer"},
                            "name": "user_id",
                            "in": "path",
                        }
                    ],
                }
            },
            "/users/{user_id}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"title": "Response", "type": "integer"}
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
                    "parameters": [
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "User Id", "type": "integer"},
                            "name": "user_id",
                            "in": "path",
                        }
                    ],
                },
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"title": "Response", "type": "integer"}
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
                    "parameters": [
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "User Id", "type": "integer"},
                            "name": "user_id",
                            "in": "path",
                        }
                    ],
                },
            },
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
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
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

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
