import typing

import pytest
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, FromPath, Path, PathParam
from xpresso.openapi.models import PathParamStyles
from xpresso.typing import Annotated


@pytest.mark.parametrize(
    "style,explode",
    [
        ("simple", True),
        ("simple", False),
        ("label", True),
        ("label", False),
        ("matrix", True),
        ("matrix", False),
    ],
)
def test_serialization(
    explode: bool,
    style: PathParamStyles,
) -> None:
    async def endpoint(
        path: Annotated[int, PathParam(style=style, explode=explode)]
    ) -> Response:
        ...

    app = App([Path("/test/{path}", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/test/{path}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
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
                            "style": style,
                            "explode": explode,
                            "schema": {"title": "Path", "type": "integer"},
                            "name": "path",
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_scalar() -> None:
    async def endpoint(path: FromPath[int]) -> Response:
        ...

    app = App([Path("/test/{path}", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/test/{path}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
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
                            "schema": {"title": "Path", "type": "integer"},
                            "name": "path",
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_array() -> None:
    async def endpoint(path: FromPath[typing.List[int]]) -> Response:
        ...

    app = App([Path("/test/{path}", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/test/{path}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
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
                            "schema": {
                                "title": "Path",
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            "name": "path",
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_object() -> None:
    class ShallowObject(BaseModel):
        foo: int
        bar: str

    async def endpoint(path: FromPath[ShallowObject]) -> Response:
        ...

    app = App([Path("/test/{path}", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/test/{path}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
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
                            "schema": {"$ref": "#/components/schemas/ShallowObject"},
                            "name": "path",
                            "in": "path",
                        }
                    ],
                }
            }
        },
        "components": {
            "schemas": {
                "ShallowObject": {
                    "title": "ShallowObject",
                    "required": ["foo", "bar"],
                    "type": "object",
                    "properties": {
                        "foo": {"title": "Foo", "type": "integer"},
                        "bar": {"title": "Bar", "type": "string"},
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_include_in_schema() -> None:
    async def endpoint(
        path: Annotated[str, PathParam(include_in_schema=False)]
    ) -> None:
        ...

    app = App([Path("/test/{path}", get=endpoint)])

    client = TestClient(app)

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/test/{path}": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            }
        },
    }

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
