from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel

from xpresso import App, Depends, FromHeader, HeaderParam, Operation, Path, Response
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


@pytest.mark.parametrize(
    "headers,status_code,json_response",
    [
        ({"Header": "123"}, 200, {"Header": "123"}),
        ({"Header": "1,2,3"}, 200, {"Header": "1"}),
        ({"Header": ""}, 200, {"Header": ""}),
    ],
)
# for scalars, explode doesn't make a difference
@pytest.mark.parametrize("explode", [True, False])
def test_scalar_string(
    headers: Optional[Dict[str, str]],
    explode: bool,
    status_code: int,
    json_response: Dict[str, Any],
) -> None:
    async def test(header: Annotated[str, HeaderParam(explode=explode)]) -> Any:
        return {"Header": header}

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)  # type: ignore[arg-type]
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response


@pytest.mark.parametrize(
    "headers,status_code,json_response",
    [
        ({"Header": "123"}, 200, {"Header": 123}),
        (
            {"Header": "1,2,3"},
            200,
            {"Header": 1},
        ),
        (
            {"Header": ""},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "Missing required header parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
    ],
)
# for scalars, explode doesn't make a difference
@pytest.mark.parametrize("explode", [True, False])
def test_scalar_int(
    headers: Optional[Dict[str, str]],
    explode: bool,
    status_code: int,
    json_response: Dict[str, Any],
) -> None:
    async def test(header: Annotated[int, HeaderParam(explode=explode)]) -> Any:
        return {"Header": header}

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)  # type: ignore[arg-type]
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response


@pytest.mark.parametrize(
    "headers,status_code,json_response",
    [
        ({"Header": "1,2"}, 200, {"Header": ["1", "2"]}),
        ({"Header": "1,2,"}, 200, {"Header": ["1", "2", ""]}),
        ({"Header": "1, 2"}, 200, {"Header": ["1", "2"]}),
        ({"Header": ""}, 200, {"Header": []}),
        ({"Header": ","}, 200, {"Header": ["", ""]}),
        ({}, 200, {"Header": []}),
    ],
)
# for header arrays, explode doesn't make a difference
@pytest.mark.parametrize("explode", [True, False])
def test_array_string(
    headers: Optional[Dict[str, str]],
    explode: bool,
    status_code: int,
    json_response: Dict[str, Any],
) -> None:
    async def test(header: Annotated[List[str], HeaderParam(explode=explode)]) -> Any:
        return {"Header": header}

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)  # type: ignore[arg-type]
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response


@pytest.mark.parametrize(
    "headers,status_code,json_response",
    [
        ({"Header": "1,2"}, 200, {"Header": [1, 2]}),
        (
            {"Header": "1,2,"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", 2],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        ({"Header": "1, 2"}, 200, {"Header": [1, 2]}),
        ({"Header": ""}, 200, {"Header": []}),
        (
            {"Header": ","},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", 0],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    },
                    {
                        "loc": ["header", "header", 1],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    },
                ]
            },
        ),
        ({}, 200, {"Header": []}),
    ],
)
# for header arrays, explode doesn't make a difference
@pytest.mark.parametrize("explode", [True, False])
def test_array_int(
    headers: Optional[Dict[str, str]],
    explode: bool,
    status_code: int,
    json_response: Dict[str, Any],
) -> None:
    async def test(header: Annotated[List[int], HeaderParam(explode=explode)]) -> Any:
        return {"Header": header}

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)  # type: ignore[arg-type]
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response


@pytest.mark.parametrize(
    "explode,headers,status_code,json_response",
    [
        # explode = True
        (True, {"Header": "foo=1,bar=2"}, 200, {"foo": 1, "bar": "2", "baz": "3"}),
        (True, {"Header": "foo=1, bar=2"}, 200, {"foo": 1, "bar": "2", "baz": "3"}),
        (
            True,
            {"Header": "foo=1,bar=2,baz=4"},
            200,
            {"foo": 1, "bar": "2", "baz": "4"},
        ),
        (
            True,
            {"Header": "foo=1abc,bar=2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "foo"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            True,
            {"Header": "foo=1,bar=2abc"},
            200,
            {"foo": 1, "bar": "2abc", "baz": "3"},
        ),
        (
            True,
            {"Header": "foo=1,baz=4"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            True,
            {"Header": "foo=1=2,bar=3"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "foo"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            True,
            {"Header": "=1,bar=3"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "invalid object style header: =1,bar=3",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        (
            True,
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "Missing required header parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        # explode = False
        (False, {"Header": "foo,1,bar,2"}, 200, {"foo": 1, "bar": "2", "baz": "3"}),
        (False, {"Header": "foo, 1, bar, 2"}, 200, {"foo": 1, "bar": "2", "baz": "3"}),
        (
            False,
            {"Header": "foo,1,bar,2,baz,4"},
            200,
            {"foo": 1, "bar": "2", "baz": "4"},
        ),
        (
            False,
            {"Header": "foo,1abc,bar,2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "foo"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            False,
            {"Header": "foo,1,bar,2abc"},
            200,
            {"foo": 1, "bar": "2abc", "baz": "3"},
        ),
        (
            False,
            {"Header": "foo,1,baz,4"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            False,
            {"Header": "foo,1,bar,3,baz"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "invalid object style header: foo,1,bar,3,baz",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        (
            False,
            {"Header": ",1,bar,3"},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            False,
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["header", "header"],
                        "msg": "Missing required header parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
    ],
)
def test_object(
    headers: Optional[Dict[str, str]],
    explode: bool,
    status_code: int,
    json_response: Dict[str, Any],
) -> None:
    class HeaderModel(BaseModel):
        foo: int
        bar: str
        baz: str = "3"

    async def test(header: Annotated[HeaderModel, HeaderParam(explode=explode)]) -> Any:
        return header

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)  # type: ignore[arg-type]
    assert resp.status_code == status_code, resp.content
    assert resp.json() == json_response


@pytest.mark.parametrize(
    "headers,convert,alias,json_response",
    [
        ({"X-MyHeader": "123"}, True, None, "123"),
        ({"X-MyHeader": "123"}, False, None, "default"),
        ({"X_MyHeader": "123"}, True, None, "default"),
        ({"X_MyHeader": "123"}, False, None, "123"),
        # with an alias that does not match
        ({"X-MyHeader": "123"}, True, "x-other", "default"),
        ({"X-MyHeader": "123"}, False, "x-other", "default"),
        ({"X_MyHeader": "123"}, True, "x-other", "default"),
        ({"X_MyHeader": "123"}, False, "x-other", "default"),
        # with an alias that matches
        ({"X-MyHeader": "123"}, True, "X-MyHeader", "123"),
        ({"X-MyHeader": "123"}, False, "X-MyHeader", "123"),
    ],
)
def test_convert_underscores(
    headers: Dict[str, str],
    convert: bool,
    alias: Optional[str],
    json_response: Any,
) -> None:
    async def test(
        x_myheader: Annotated[
            str, HeaderParam(convert_underscores=convert, alias=alias)
        ] = "default"
    ) -> str:
        return x_myheader

    app = App([Path("/", get=test)])

    client = TestClient(app)

    resp = client.get("/", headers=headers)
    assert resp.status_code == 200, resp.content
    assert resp.json() == json_response


def test_parameter_is_used_in_multiple_locations() -> None:
    async def dep(param: FromHeader[str]) -> None:
        ...

    async def endpoint(param: FromHeader[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint, dependencies=[Depends(dep)]))])

    client = TestClient(app)

    resp = client.get("/", headers={"param": "foo"})
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
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Param", "type": "string"},
                            "name": "param",
                            "in": "header",
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


def test_multiple_parameters() -> None:
    async def endpoint(param1: FromHeader[str], param2: FromHeader[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint))])

    client = TestClient(app)

    resp = client.get("/", headers={"param1": "foo", "param2": "bar"})
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
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Param1", "type": "string"},
                            "name": "param1",
                            "in": "header",
                        },
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Param2", "type": "string"},
                            "name": "param2",
                            "in": "header",
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
        header: Annotated[int, HeaderParam(explode=explode)]
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
                            "style": "simple",
                            "explode": explode,
                            "schema": {"title": "Header", "type": "integer"},
                            "name": "header",
                            "in": "header",
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
    async def endpoint(header: FromHeader[int]) -> Response:
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
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Header", "type": "integer"},
                            "name": "header",
                            "in": "header",
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
    async def endpoint(header: FromHeader[List[int]]) -> Response:
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
                            "style": "simple",
                            "explode": False,
                            "schema": {
                                "title": "Header",
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            "name": "header",
                            "in": "header",
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

    async def endpoint(header: FromHeader[ShallowObject]) -> Response:
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
                            "style": "simple",
                            "explode": False,
                            "schema": {"$ref": "#/components/schemas/ShallowObject"},
                            "name": "header",
                            "in": "header",
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
    async def endpoint(header: FromHeader[int] = 2) -> Response:
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
                            "style": "simple",
                            "explode": False,
                            "schema": {
                                "title": "Header",
                                "type": "integer",
                                "default": 2,
                            },
                            "name": "header",
                            "in": "header",
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
    async def endpoint(header: FromHeader[Optional[int]]) -> Response:
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
                            "style": "simple",
                            "explode": False,
                            "schema": {
                                "title": "Header",
                                "type": "integer",
                                "nullable": True,
                            },
                            "name": "header",
                            "in": "header",
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
        x_header: Annotated[str, HeaderParam(include_in_schema=False)]
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
