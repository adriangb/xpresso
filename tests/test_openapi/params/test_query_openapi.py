import typing

import pytest
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, FromQuery, Path, QueryParam
from xpresso.openapi.models import QueryParamStyles
from xpresso.typing import Annotated


@pytest.mark.parametrize(
    "style,explode",
    [
        ("form", True),
        ("form", False),
        ("spaceDelimited", True),
        ("spaceDelimited", False),
        ("pipeDelimited", True),
        ("pipeDelimited", False),
        ("deepObject", True),
    ],
)
def test_serialization(
    explode: bool,
    style: QueryParamStyles,
) -> None:
    async def endpoint(
        query: Annotated[int, QueryParam(style=style, explode=explode)]
    ) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "schema": {"title": "Query", "type": "integer"},
                            "name": "query",
                            "in": "query",
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
    async def endpoint(query: FromQuery[int]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Query", "type": "integer"},
                            "name": "query",
                            "in": "query",
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
    async def endpoint(query: FromQuery[typing.List[int]]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Query",
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            "name": "query",
                            "in": "query",
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

    async def endpoint(query: FromQuery[ShallowObject]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "style": "form",
                            "explode": True,
                            "schema": {"$ref": "#/components/schemas/ShallowObject"},
                            "name": "query",
                            "in": "query",
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


def test_non_nullable_with_default() -> None:
    class ShallowObject(BaseModel):
        foo: int
        bar: str

    async def endpoint(
        query: FromQuery[ShallowObject] = ShallowObject(foo=1, bar="2")
    ) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "required": False,
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Query",
                                "allOf": [
                                    {"$ref": "#/components/schemas/ShallowObject"}
                                ],
                                "default": {"foo": 1, "bar": "2"},
                            },
                            "name": "query",
                            "in": "query",
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


def test_nullable_without_default() -> None:
    async def endpoint(query: FromQuery[typing.Optional[int]]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Query",
                                "type": "integer",
                                "nullable": True,
                            },
                            "name": "query",
                            "in": "query",
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


def test_nullable_with_default() -> None:
    async def endpoint(query: FromQuery[typing.Optional[int]] = None) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                            "required": False,
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Query",
                                "type": "integer",
                                "nullable": True,
                            },
                            "name": "query",
                            "in": "query",
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
