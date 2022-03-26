from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from xpresso import App, Depends, FromPath, Operation, Path, PathParam, Response
from xpresso.openapi.models import PathParamStyles
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


@pytest.mark.parametrize(
    "style,explode,param,status_code,expected_json_response",
    [
        # simple, True
        ("simple", True, "5", 200, "5"),
        ("simple", True, "3,4,5", 200, "3,4,5"),
        # simple, False
        ("simple", False, "5", 200, "5"),
        ("simple", False, "3,4,5", 200, "3,4,5"),
        # label, True
        ("label", True, ".5", 200, "5"),
        ("label", True, ".3,4,5", 200, "3,4,5"),
        (
            "label",
            False,
            "3",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "label serialized parameter must start with '.'",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # label, False
        ("label", False, ".5", 200, "5"),
        ("label", False, ".3,4,5", 200, "3,4,5"),
        (
            "label",
            False,
            "3",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "label serialized parameter must start with '.'",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, True
        ("matrix", True, ";param=5", 200, "5"),
        ("matrix", True, ";param=3,4,5", 200, "3,4,5"),
        (
            "matrix",
            True,
            ";notparam=5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, False
        ("matrix", False, ";param=5", 200, "5"),
        ("matrix", False, ";param=3,4,5", 200, "3,4,5"),
        (
            "matrix",
            False,
            ";notparam=5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
    ],
)
def test_scalar_string(
    style: PathParamStyles,
    explode: bool,
    param: str,
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[str, PathParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    response = client.get(f"{param}")
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,param,status_code,expected_json_response",
    [
        # simple, True
        ("simple", True, "5", 200, 5),
        (
            "simple",
            True,
            "3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # simple, False
        ("simple", False, "5", 200, 5),
        (
            "simple",
            False,
            "3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # label, True
        ("label", True, ".5", 200, 5),
        (
            "label",
            True,
            ".3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # label, False
        ("label", False, ".5", 200, 5),
        (
            "label",
            False,
            ".3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # matrix, True
        ("matrix", True, ";param=5", 200, 5),
        (
            "matrix",
            True,
            ";param=3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            "matrix",
            True,
            ";notparam=5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, False
        ("matrix", False, ";param=5", 200, 5),
        (
            "matrix",
            False,
            ";param=3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            "matrix",
            False,
            ";notparam=5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
    ],
)
def test_scalar_int(
    style: PathParamStyles,
    explode: bool,
    param: str,
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[int, PathParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    response = client.get(f"{param}")
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,param,status_code,expected_json_response",
    [
        # simple, True
        ("simple", True, "5", 200, ["5"]),
        ("simple", True, "3,4,5", 200, ["3", "4", "5"]),
        ("simple", True, ",4,5", 200, ["", "4", "5"]),
        # simple, False
        ("simple", False, "5", 200, ["5"]),
        ("simple", False, "3,4,5", 200, ["3", "4", "5"]),
        ("simple", True, ",4,5", 200, ["", "4", "5"]),
        # label, True
        ("label", True, ".5", 200, ["5"]),
        ("label", True, ".3.4.5", 200, ["3", "4", "5"]),
        ("label", True, ".3,4,5", 200, ["3,4,5"]),
        (
            "label",
            True,
            "3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "label serialized parameter must start with '.'",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # label, False
        ("label", False, ".5", 200, ["5"]),
        ("label", False, ".3.4.5", 200, ["3.4.5"]),
        ("label", False, ".3,4,5", 200, ["3", "4", "5"]),
        (
            "label",
            False,
            "3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "label serialized parameter must start with '.'",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, True
        ("matrix", True, ";param=5", 200, ["5"]),
        ("matrix", True, ";param=3;param=4;param=5", 200, ["3", "4", "5"]),
        ("matrix", True, ";param=3,4,5", 200, ["3,4,5"]),
        (
            "matrix",
            True,
            ";notparam=3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, False
        ("matrix", False, ";param=5", 200, ["5"]),
        ("matrix", False, ";param=3;param=4;param=5", 200, ["3;param=4;param=5"]),
        ("matrix", False, ";param=3,4,5", 200, ["3", "4", "5"]),
        (
            "matrix",
            False,
            ";not=3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "matrix serialized parameter must start with ;param=",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
    ],
)
def test_array_string(
    style: PathParamStyles,
    explode: bool,
    param: str,
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[List[str], PathParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    response = client.get(f"{param}")
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,param,status_code,expected_json_response",
    [
        # simple, True
        ("simple", True, "5", 200, [5]),
        ("simple", True, "3,4,5", 200, [3, 4, 5]),
        # simple, False
        ("simple", False, "5", 200, [5]),
        ("simple", False, "3,4,5", 200, [3, 4, 5]),
        # label, True
        ("label", True, ".5", 200, [5]),
        ("label", True, ".3.4.5", 200, [3, 4, 5]),
        (
            "label",
            True,
            ".3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param", 0],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # label, False
        ("label", False, ".5", 200, [5]),
        (
            "label",
            False,
            ".3.4.5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param", 0],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        ("label", False, ".3,4,5", 200, [3, 4, 5]),
        # matrix, True
        ("matrix", True, ";param=5", 200, [5]),
        ("matrix", True, ";param=3;param=4;param=5", 200, [3, 4, 5]),
        (
            "matrix",
            True,
            ";param=3,4,5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param", 0],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # matrix, False
        ("matrix", False, ";param=5", 200, [5]),
        (
            "matrix",
            False,
            ";param=3;param=4;param=5",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param", 0],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        ("matrix", False, ";param=3,4,5", 200, [3, 4, 5]),
    ],
)
def test_array_int(
    style: PathParamStyles,
    explode: bool,
    param: str,
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[List[int], PathParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    response = client.get(f"{param}")
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,param,status_code,expected_json_response",
    [
        # simple, True
        ("simple", True, "foo=1,bar=2", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("simple", True, "bar=2,foo=1", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("simple", True, "foo=1,bar=2,baz=4", 200, {"foo": "1", "bar": 2, "baz": "4"}),
        # simple, False
        ("simple", False, "foo,1,bar,2", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("simple", False, "bar,2,foo,1", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("simple", False, "foo,1,bar,2,baz,4", 200, {"foo": "1", "bar": 2, "baz": "4"}),
        # label, True
        ("label", True, ".foo=1.bar=2", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("label", True, ".bar=2.foo=1", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("label", True, ".foo=1.bar=2.baz=4", 200, {"foo": "1", "bar": 2, "baz": "4"}),
        # label, False
        ("label", False, ".foo,1,bar,2", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("label", False, ".bar,2,foo,1", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("label", False, ".foo,1,bar,2,baz,4", 200, {"foo": "1", "bar": 2, "baz": "4"}),
        # matrix, True
        ("matrix", True, ";foo=1;bar=2", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        ("matrix", True, ";bar=2;foo=1", 200, {"foo": "1", "bar": 2, "baz": "3"}),
        (
            "matrix",
            True,
            ";foo=1;bar=2;baz=4",
            200,
            {"foo": "1", "bar": 2, "baz": "4"},
        ),
        (
            "matrix",
            True,
            "foo=1;bar=2",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "object-valued path parameter could be deserialized with style=matrix, explode=True: foo=1;bar=2",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        (
            "matrix",
            True,
            ";foo;bar=2",
            422,
            {
                "detail": [
                    {
                        "loc": ["path", "param"],
                        "msg": "foo is not a valid field encoding",
                        "type": "value_error.invalidserialization",
                    }
                ]
            },
        ),
        # matrix, False
        (
            "matrix",
            False,
            ";param=foo,1,bar,2",
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "matrix",
            False,
            ";param=bar,2,foo,1",
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "matrix",
            False,
            ";param=foo,1,bar,2,baz,4",
            200,
            {"foo": "1", "bar": 2, "baz": "4"},
        ),
    ],
)
def test_object(
    style: PathParamStyles,
    explode: bool,
    param: str,
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    class Model(BaseModel):
        foo: str
        bar: int
        baz: str = "3"

    async def endpoint(
        param: Annotated[Model, PathParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    response = client.get(f"{param}")
    assert response.status_code == status_code
    assert response.json() == expected_json_response


def test_default_value_raises_exception() -> None:
    async def endpoint(param: FromPath[str] = "123") -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/{param}", get=endpoint)])

    client = TestClient(app)

    with pytest.raises(
        TypeError,
        match="Path parameters MUST be required and MUST NOT have default values",
    ):
        client.get("/1234")


def test_parameter_is_used_in_multiple_locations() -> None:
    async def dep(param: FromPath[str]) -> None:
        ...

    async def endpoint(param: FromPath[str]) -> None:
        ...

    app = App(
        [Path("/foo/{param}", get=Operation(endpoint, dependencies=[Depends(dep)]))]
    )

    client = TestClient(app)

    resp = client.get("/foo/bar")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/foo/{param}": {
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


def test_multiple_parameters() -> None:
    async def endpoint(param1: FromPath[str], param2: FromPath[str]) -> None:
        ...

    app = App([Path("/{param1}/{param2}", get=Operation(endpoint))])

    client = TestClient(app)

    resp = client.get("/foo/bar")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/{param1}/{param2}": {
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
                            "in": "path",
                        },
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {"title": "Param2", "type": "string"},
                            "name": "param2",
                            "in": "path",
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
