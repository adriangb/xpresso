"""Tests for experimental OpenAPI inspired routing"""
from typing import Any, Dict

import pytest

from xpresso import App, FromPath, Path, Request
from xpresso.routing.mount import Mount
from xpresso.testclient import TestClient


async def endpoint(number: FromPath[int]) -> int:
    return number + 1


def test_routing_for_mounted_path() -> None:
    app = App(
        routes=[
            Mount(
                path="/mount",
                routes=[
                    Path(
                        path="/{number}",
                        get=endpoint,
                    )
                ],
            )
        ]
    )

    client = TestClient(app)

    resp = client.get("/mount/123")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 124


def test_openapi_routing_for_mounted_path() -> None:
    app = App(
        routes=[
            Mount(
                path="/mount",
                routes=[
                    Path(
                        path="/{number}",
                        get=endpoint,
                    )
                ],
            )
        ]
    )

    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/mount/{number}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
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
                            "schema": {"title": "Number", "type": "integer"},
                            "name": "number",
                            "in": "path",
                        }
                    ],
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


def test_mounted_xpresso_app_routing() -> None:
    # not a use case we advertise
    # but we want to know what the behavior is
    app = App(
        routes=[
            Mount(
                path="/mount",
                app=App(
                    routes=[
                        Path(
                            path="/{number}",
                            get=endpoint,
                        )
                    ]
                ),
            )
        ]
    )

    client = TestClient(app)

    resp = client.get("/mount/123")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 124


def test_mounted_xpresso_app_openapi() -> None:
    # not a use case we advertise
    # but we want to know what the behavior is
    app = App(
        routes=[
            Mount(
                path="/mount",
                app=App(
                    routes=[
                        Path(
                            path="/{number}",
                            get=endpoint,
                        )
                    ]
                ),
            )
        ]
    )

    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/mount/{number}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Successful Response",
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
                            "schema": {"title": "Number", "type": "integer"},
                            "name": "number",
                            "in": "path",
                        }
                    ],
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


def test_mounted_xpresso_app_dependencies_isolated_containers() -> None:
    # not a use case we advertise
    # but we want to know what the behavior is

    class Thing:
        def __init__(self, value: str = "default") -> None:
            self.value = value

    async def endpoint(thing: Thing) -> str:
        return thing.value

    inner_app = App(
        routes=[
            Path(
                path="/",
                get=endpoint,
            )
        ],
    )

    app = App(
        routes=[
            Mount(
                path="/mount",
                app=inner_app,
            ),
            Path("/top-level", get=endpoint),
        ]
    )

    app.dependency_overrides[Thing] = lambda: Thing("injected")

    client = TestClient(app)

    resp = client.get("/top-level")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "injected"

    resp = client.get("/mount")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "default"


def test_mounted_xpresso_app_dependencies_shared_containers() -> None:
    # not a use case we advertise
    # but we want to know what the behavior is

    class Thing:
        def __init__(self, value: str = "default") -> None:
            self.value = value

    async def endpoint(thing: Thing) -> str:
        return thing.value

    inner_app = App(
        routes=[
            Path(
                path="/",
                get=endpoint,
            )
        ],
    )
    inner_app.dependency_overrides[Thing] = lambda: Thing("injected")

    app = App(
        routes=[
            Mount(
                path="/mount",
                app=inner_app,
            ),
            Path("/top-level", get=endpoint),
        ],
        container=inner_app.container,
    )

    client = TestClient(app)

    resp = client.get("/top-level")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "injected"

    resp = client.get("/mount")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "injected"


@pytest.mark.parametrize(
    "root_path_outer,root_path_inner,client_path,expected",
    [
        ("", "", "/mount/app", "/mount"),
        ("/v1/api", "", "/mount/app", "/v1/api/mount"),
        ("", "/v1/api", "/mount/app", "/mount/v1/api"),
        ("/v1/api", "/foo/bar", "/mount/app", "/v1/api/mount/foo/bar"),
    ],
)
def test_root_path_on_mounts(
    root_path_outer: str,
    root_path_inner: str,
    client_path: str,
    expected: str,
) -> None:
    async def endpoint(request: Request) -> str:
        return request.scope["root_path"]

    inner_app = App(
        routes=[Path(path="/app", get=endpoint, name="inner-app")],
        root_path=root_path_inner,
    )

    app = App(
        routes=[
            Mount(
                path="/mount",
                app=inner_app,
            ),
        ],
        root_path=root_path_outer,
    )

    client = TestClient(app)

    resp = client.get(client_path)

    assert resp.status_code == 200, resp.content
    assert resp.json() == expected
