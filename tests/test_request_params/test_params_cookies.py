from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel

from xpresso import App, CookieParam, Depends, FromCookie, Operation, Path, Response
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        (None, 200, {"cookie": None}),
        ({"cookie": "123"}, 200, {"cookie": 123}),
        (
            {"cookie": "123", "notcookie": "456"},
            200,
            {"cookie": 123},
        ),
        ({"notcookie": "456"}, 200, {"cookie": None}),
        (
            {"cookie": "abc"},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
    ],
)
def test_with_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    async def test(cookie: FromCookie[Optional[int]] = None) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        ({"cookie": "123"}, 200, {"cookie": 123}),
        (
            {"notcookie": "456"},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "Missing required cookie parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        (
            None,
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "Missing required cookie parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
    ],
)
def test_without_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    async def test(cookie: FromCookie[Optional[int]]) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        ({"cookie": "123"}, 200, {"cookie": 123}),
        (
            None,
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "Missing required cookie parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        (
            {"cookie": "123,"},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
    ],
)
def test_explode_false_scalar(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    async def test(cookie: Annotated[Optional[int], CookieParam(explode=True)]) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        ({"cookie": "123"}, 200, {"cookie": [123]}),
        ({"cookie": "123,123"}, 200, {"cookie": [123, 123]}),
        ({"cookie": ""}, 200, {"cookie": []}),
        ({"cookie": "123,"}, 200, {"cookie": [123]}),
        (
            {"cookie": "123,abc,"},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie", 1],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            None,
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "Missing required cookie parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
    ],
)
def test_explode_false_array_without_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    async def test(cookie: Annotated[List[int], CookieParam(explode=False)]) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        (None, 200, {"cookie": None}),
    ],
)
def test_explode_false_array_with_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    async def test(
        cookie: Annotated[Optional[List[int]], CookieParam(explode=False)] = None
    ) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        ({"cookie": "a,1,b,2"}, 200, {"cookie": {"a": 1, "b": "2"}}),
        (
            {"cookie": "a,abcd,b,2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie", "a"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            None,
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie"],
                        "msg": "Missing required cookie parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        (
            {"cookie": ""},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie", "a"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["cookie", "cookie", "b"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
    ],
)
def test_explode_false_object_without_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    class MyCookie(BaseModel):
        a: int
        b: str

    async def test(cookie: Annotated[MyCookie, CookieParam(explode=False)]) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


@pytest.mark.parametrize(
    "cookies, expected_status_code, expected_response",
    [
        (None, 200, {"cookie": None}),
        (
            {"cookie": ""},
            422,
            {
                "detail": [
                    {
                        "loc": ["cookie", "cookie", "a"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["cookie", "cookie", "b"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
    ],
)
def test_explode_false_object_with_default_value(
    cookies: Dict[str, str],
    expected_status_code: int,
    expected_response: Dict[str, Any],
) -> None:
    class MyCookie(BaseModel):
        a: int
        b: str

    async def test(
        cookie: Annotated[Optional[MyCookie], CookieParam(explode=False)] = None
    ) -> Any:
        return {"cookie": cookie}

    app = App([Path("/", get=test)])

    with TestClient(app) as client:
        resp = client.get("/", cookies=cookies)
    assert resp.status_code == expected_status_code, resp.text
    assert resp.json() == expected_response


def test_parameter_is_used_in_multiple_locations() -> None:
    async def dep(param: FromCookie[str]) -> None:
        ...

    async def endpoint(param: FromCookie[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint, dependencies=[Depends(dep)]))])

    client = TestClient(app)

    resp = client.get("/", cookies={"param": "foo"})
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Param", "type": "string"},
                            "name": "param",
                            "in": "cookie",
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

    {
        "components": {
            "schemas": {
                "HTTPValidationError": {
                    "properties": {
                        "detail": {
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                            "title": "Detail",
                            "type": "array",
                        }
                    },
                    "title": "HTTPValidationError",
                    "type": "object",
                },
                "ValidationError": {
                    "properties": {
                        "loc": {
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                            "title": "Location",
                            "type": "array",
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                    "required": ["loc", "msg", "type"],
                    "title": "ValidationError",
                    "type": "object",
                },
            }
        },
        "info": {"title": "API", "version": "0.1.0"},
        "openapi": "3.0.3",
        "paths": {
            "/": {
                "get": {
                    "parameters": [
                        {
                            "explode": True,
                            "in": "cookie",
                            "name": "param",
                            "required": True,
                            "schema": {"title": "Param", "type": "string"},
                            "style": "form",
                        },
                        {
                            "explode": True,
                            "in": "cookie",
                            "name": "param",
                            "required": True,
                            "schema": {"title": "Param", "type": "string"},
                            "style": "form",
                        },
                        {
                            "explode": True,
                            "in": "cookie",
                            "name": "param",
                            "required": True,
                            "schema": {"title": "Param", "type": "string"},
                            "style": "form",
                        },
                    ],
                    "responses": {
                        "200": {
                            "content": {"application/json": {}},
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
    }

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_multiple_parameters() -> None:
    async def endpoint(param1: FromCookie[str], param2: FromCookie[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint))])

    client = TestClient(app)

    resp = client.get("/", cookies={"param1": "foo", "param2": "bar"})
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Param1", "type": "string"},
                            "name": "param1",
                            "in": "cookie",
                        },
                        {
                            "required": True,
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Param2", "type": "string"},
                            "name": "param2",
                            "in": "cookie",
                        },
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


@pytest.mark.parametrize(
    "explode",
    [True, False],
)
def test_openapi_serialization(
    explode: bool,
) -> None:
    async def endpoint(
        cookie: Annotated[int, CookieParam(explode=explode)]
    ) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": explode,
                            "schema": {"title": "Cookie", "type": "integer"},
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_scalar() -> None:
    async def endpoint(cookie: FromCookie[int]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Cookie", "type": "integer"},
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_array() -> None:
    async def endpoint(
        # arrays only work with explode=False
        cookie: Annotated[List[int], CookieParam(explode=False)]
    ) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": False,
                            "schema": {
                                "title": "Cookie",
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_object() -> None:
    class ShallowObject(BaseModel):
        foo: int
        bar: str

    async def endpoint(
        # objects only work with explode=False
        cookie: Annotated[ShallowObject, CookieParam(explode=False)]
    ) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": False,
                            "schema": {"$ref": "#/components/schemas/ShallowObject"},
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_default() -> None:
    async def endpoint(cookie: FromCookie[int] = 2) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Cookie",
                                "type": "integer",
                                "default": 2,
                            },
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_nullable() -> None:
    async def endpoint(cookie: FromCookie[Optional[int]]) -> Response:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "title": "Cookie",
                                "type": "integer",
                                "nullable": True,
                            },
                            "name": "cookie",
                            "in": "cookie",
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


def test_openapi_include_in_schema() -> None:
    async def endpoint(
        cookie: Annotated[str, CookieParam(include_in_schema=False)]
    ) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
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
