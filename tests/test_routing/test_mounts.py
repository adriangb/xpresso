"""Tests for experimental OpenAPI inspired routing"""
from typing import Any, Dict

from di import BaseContainer

from xpresso import App, Dependant, FromPath, Path
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

    app.container.register_by_type(
        Dependant(lambda: Thing("injected")),
        Thing,
    )

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

    container = BaseContainer(scopes=("app", "connection", "operation"))
    container.register_by_type(
        Dependant(lambda: Thing("injected")),
        Thing,
    )

    inner_app = App(
        routes=[
            Path(
                path="/",
                get=endpoint,
            )
        ],
        container=container,
    )

    app = App(
        routes=[
            Mount(
                path="/mount",
                app=inner_app,
            ),
            Path("/top-level", get=endpoint),
        ],
        container=container,
    )

    client = TestClient(app)

    resp = client.get("/top-level")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "injected"

    resp = client.get("/mount")
    assert resp.status_code == 200, resp.content
    assert resp.json() == "injected"
