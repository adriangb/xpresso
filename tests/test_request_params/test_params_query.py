from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel

from xpresso import App, Depends, FromQuery, Operation, Path, QueryParam, Response
from xpresso.openapi.models import QueryParamStyles
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

missing_error = {
    "detail": [
        {
            "loc": ["query", "param"],
            "msg": "Missing required query parameter",
            "type": "value_error",
        }
    ]
}


invalid_serialization_error = {
    "detail": [
        {
            "loc": ["query", "param"],
            "msg": "Data is not a valid URL encoded query",
            "type": "type_error",
        }
    ]
}

scalar_non_nullable_error = {
    "detail": [
        {
            "loc": ["query", "param"],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]
}


array_non_nullable_error = {
    "detail": [
        {
            "loc": ["query", "param", 0],
            "msg": "none is not an allowed value",
            "type": "type_error.none.not_allowed",
        }
    ]
}


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, "apple"),
        ("form", True, {"param": "apple,hammer"}, 200, "apple,hammer"),
        (
            "form",
            True,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
        # form, False
        ("form", False, {"param": "apple"}, 200, "apple"),
        ("form", False, {"param": "apple,hammer"}, 200, "apple,hammer"),
        (
            "form",
            False,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            False,
            {},
            422,
            missing_error,
        ),
    ],
)
def test_scalar_string_required_non_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[str, QueryParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, "apple"),
        ("form", True, {"param": "apple,hammer"}, 200, "apple,hammer"),
        ("form", True, {"param": ""}, 200, None),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
        # form, False
        ("form", False, {"param": "apple"}, 200, "apple"),
        ("form", False, {"param": "apple,hammer"}, 200, "apple,hammer"),
        ("form", False, {"param": ""}, 200, None),
        (
            "form",
            False,
            {},
            422,
            missing_error,
        ),
    ],
)
def test_scalar_string_required_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[Optional[str], QueryParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, "apple"),
        ("form", True, {"param": "apple,hammer"}, 200, "apple,hammer"),
        (
            "form",
            True,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            True,
            {},
            200,
            "default",
        ),
        # form, False
        ("form", False, {"param": "apple"}, 200, "apple"),
        ("form", False, {"param": "apple,hammer"}, 200, "apple,hammer"),
        (
            "form",
            False,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            False,
            {},
            200,
            "default",
        ),
    ],
)
def test_scalar_string_optional_non_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[str, QueryParam(style=style, explode=explode)] = "default"
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, "apple"),
        ("form", True, {"param": "apple,hammer"}, 200, "apple,hammer"),
        ("form", True, {"param": ""}, 200, None),
        (
            "form",
            True,
            {},
            200,
            "default",
        ),
        # form, False
        ("form", False, {"param": "apple"}, 200, "apple"),
        ("form", False, {"param": "apple,hammer"}, 200, "apple,hammer"),
        ("form", False, {"param": ""}, 200, None),
        (
            "form",
            False,
            {},
            200,
            "default",
        ),
    ],
)
def test_scalar_string_optional_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[
            Optional[str], QueryParam(style=style, explode=explode)
        ] = "default"
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


scalar_not_a_valid_integer_error = {
    "detail": [
        {
            "loc": ["query", "param"],
            "msg": "value is not a valid integer",
            "type": "type_error.integer",
        }
    ]
}


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, 1),
        (
            "form",
            True,
            {"param": "1,2"},
            422,
            scalar_not_a_valid_integer_error,
        ),
        (
            "form",
            True,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
        # form, False
        ("form", False, {"param": "1"}, 200, 1),
        (
            "form",
            True,
            {"param": "1,2"},
            422,
            scalar_not_a_valid_integer_error,
        ),
        (
            "form",
            True,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
    ],
)
def test_scalar_integer_required_non_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[int, QueryParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, 1),
        (
            "form",
            True,
            {"param": "1,2"},
            422,
            scalar_not_a_valid_integer_error,
        ),
        (
            "form",
            True,
            {"param": ""},
            200,
            None,
        ),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
        # form, False
        ("form", False, {"param": "1"}, 200, 1),
        (
            "form",
            True,
            {"param": "1,2"},
            422,
            scalar_not_a_valid_integer_error,
        ),
        (
            "form",
            True,
            {"param": ""},
            200,
            None,
        ),
        (
            "form",
            True,
            {},
            422,
            missing_error,
        ),
    ],
)
def test_scalar_integer_required_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[Optional[int], QueryParam(style=style, explode=explode)]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, 1),
        ("form", True, {"param": "1,2"}, 422, scalar_not_a_valid_integer_error),
        (
            "form",
            True,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            True,
            {},
            200,
            -1,
        ),
        # form, False
        ("form", False, {"param": "1"}, 200, 1),
        ("form", False, {"param": "1,2"}, 422, scalar_not_a_valid_integer_error),
        (
            "form",
            False,
            {"param": ""},
            422,
            scalar_non_nullable_error,
        ),
        (
            "form",
            False,
            {},
            200,
            -1,
        ),
    ],
)
def test_scalar_integer_optional_non_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[int, QueryParam(style=style, explode=explode)] = -1
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, 1),
        ("form", True, {"param": "1,2"}, 422, scalar_not_a_valid_integer_error),
        (
            "form",
            True,
            {"param": ""},
            200,
            None,
        ),
        (
            "form",
            True,
            {},
            200,
            -1,
        ),
        # form, False
        ("form", False, {"param": "1"}, 200, 1),
        ("form", False, {"param": "1,2"}, 422, scalar_not_a_valid_integer_error),
        (
            "form",
            False,
            {"param": ""},
            200,
            None,
        ),
        (
            "form",
            False,
            {},
            200,
            -1,
        ),
    ],
)
def test_scalar_integer_optional_nullable(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[Optional[int], QueryParam(style=style, explode=explode)] = -1
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, ["apple"]),
        (
            "form",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("form", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("form", True, {"param": ""}, 422, array_non_nullable_error),
        ("form", True, {}, 200, []),
        # form, False
        ("form", False, {"param": "apple"}, 200, ["apple"]),
        (
            "form",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("form", False, {"param": "apple,hammer"}, 200, ["apple", "hammer"]),
        ("form", False, {"param": ""}, 422, array_non_nullable_error),
        ("form", False, {}, 200, []),
        # spaceDelimited, True
        ("spaceDelimited", True, {"param": "apple"}, 200, ["apple"]),
        (
            "spaceDelimited",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("spaceDelimited", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("spaceDelimited", True, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("spaceDelimited", True, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("spaceDelimited", True, {"param": ""}, 422, array_non_nullable_error),
        ("spaceDelimited", True, {}, 200, []),
        # spaceDelimited, False
        ("spaceDelimited", False, {"param": "apple"}, 200, ["apple"]),
        (
            "spaceDelimited",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("spaceDelimited", False, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("spaceDelimited", False, {"param": "apple hammer"}, 200, ["apple", "hammer"]),
        ("spaceDelimited", False, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("spaceDelimited", False, {"param": ""}, 422, array_non_nullable_error),
        ("spaceDelimited", False, {}, 200, []),
        # pipeDelimited, True
        ("pipeDelimited", True, {"param": "apple"}, 200, ["apple"]),
        (
            "pipeDelimited",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("pipeDelimited", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("pipeDelimited", True, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("pipeDelimited", True, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("pipeDelimited", True, {"param": ""}, 422, array_non_nullable_error),
        ("pipeDelimited", True, {}, 200, []),
        # pipeDelimited, False
        ("pipeDelimited", False, {"param": "apple"}, 200, ["apple"]),
        (
            "pipeDelimited",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("pipeDelimited", False, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("pipeDelimited", False, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("pipeDelimited", False, {"param": "apple|hammer"}, 200, ["apple", "hammer"]),
        ("pipeDelimited", False, {"param": ""}, 422, array_non_nullable_error),
        ("pipeDelimited", False, {}, 200, []),
    ],
)
def test_string_array_non_nullable_items(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[
            List[str], QueryParam(style=style, explode=explode)
        ],  # type: ignore[arg-type]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "apple"}, 200, ["apple"]),
        (
            "form",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("form", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("form", True, {"param": ""}, 200, [None]),
        ("form", True, {}, 200, []),
        # form, False
        ("form", False, {"param": "apple"}, 200, ["apple"]),
        (
            "form",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("form", False, {"param": "apple,hammer"}, 200, ["apple", "hammer"]),
        ("form", False, {"param": ""}, 200, [None]),
        ("form", False, {}, 200, []),
        # spaceDelimited, True
        ("spaceDelimited", True, {"param": "apple"}, 200, ["apple"]),
        (
            "spaceDelimited",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("spaceDelimited", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("spaceDelimited", True, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("spaceDelimited", True, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("spaceDelimited", True, {"param": ""}, 200, [None]),
        ("spaceDelimited", True, {}, 200, []),
        # spaceDelimited, False
        ("spaceDelimited", False, {"param": "apple"}, 200, ["apple"]),
        (
            "spaceDelimited",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("spaceDelimited", False, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("spaceDelimited", False, {"param": "apple hammer"}, 200, ["apple", "hammer"]),
        ("spaceDelimited", False, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("spaceDelimited", False, {"param": ""}, 200, [None]),
        ("spaceDelimited", False, {}, 200, []),
        # pipeDelimited, True
        ("pipeDelimited", True, {"param": "apple"}, 200, ["apple"]),
        (
            "pipeDelimited",
            True,
            [("param", "apple"), ("param", "hammer")],
            200,
            ["apple", "hammer"],
        ),
        ("pipeDelimited", True, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("pipeDelimited", True, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("pipeDelimited", True, {"param": "apple|hammer"}, 200, ["apple|hammer"]),
        ("pipeDelimited", True, {"param": ""}, 200, [None]),
        ("pipeDelimited", True, {}, 200, []),
        # pipeDelimited, False
        ("pipeDelimited", False, {"param": "apple"}, 200, ["apple"]),
        (
            "pipeDelimited",
            False,
            [("param", "apple"), ("param", "hammer")],
            422,
            invalid_serialization_error,
        ),
        ("pipeDelimited", False, {"param": "apple,hammer"}, 200, ["apple,hammer"]),
        ("pipeDelimited", False, {"param": "apple hammer"}, 200, ["apple hammer"]),
        ("pipeDelimited", False, {"param": "apple|hammer"}, 200, ["apple", "hammer"]),
        ("pipeDelimited", False, {"param": ""}, 200, [None]),
        ("pipeDelimited", False, {}, 200, []),
    ],
)
def test_string_array_nullable_items(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[
            List[Optional[str]], QueryParam(style=style, explode=explode)
        ],  # type: ignore[arg-type]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


array_not_a_valid_integer_error = {
    "detail": [
        {
            "loc": ["query", "param", 0],
            "msg": "value is not a valid integer",
            "type": "type_error.integer",
        }
    ]
}


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, [1]),
        (
            "form",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        ("form", True, {"param": "1,2"}, 422, array_not_a_valid_integer_error),
        ("form", True, {"param": ""}, 422, array_non_nullable_error),
        ("form", True, {}, 200, []),
        # form, False
        ("form", False, {"param": "1"}, 200, [1]),
        (
            "form",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        ("form", False, {"param": "1,2"}, 200, [1, 2]),
        ("form", False, {"param": ""}, 422, array_non_nullable_error),
        ("form", False, {}, 200, []),
        # spaceDelimited, True
        ("spaceDelimited", True, {"param": "1"}, 200, [1]),
        (
            "spaceDelimited",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1 2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1|2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", True, {"param": ""}, 422, array_non_nullable_error),
        ("spaceDelimited", True, {}, 200, []),
        # spaceDelimited, False
        ("spaceDelimited", False, {"param": "1"}, 200, [1]),
        (
            "spaceDelimited",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        (
            "spaceDelimited",
            False,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", False, {"param": "1 2"}, 200, [1, 2]),
        (
            "spaceDelimited",
            False,
            {"param": "1|2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", False, {"param": ""}, 422, array_non_nullable_error),
        ("spaceDelimited", False, {}, 200, []),
        # pipeDelimited, True
        ("pipeDelimited", True, {"param": "1"}, 200, [1]),
        (
            "pipeDelimited",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        ("pipeDelimited", True, {"param": "1,2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": "1 2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": "1|2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": ""}, 422, array_non_nullable_error),
        ("pipeDelimited", True, {}, 200, []),
        # pipeDelimited, False
        ("pipeDelimited", False, {"param": "1"}, 200, [1]),
        (
            "pipeDelimited",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        (
            "pipeDelimited",
            False,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "pipeDelimited",
            False,
            {"param": "1 2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("pipeDelimited", False, {"param": "1|2"}, 200, [1, 2]),
        ("pipeDelimited", False, {"param": ""}, 422, array_non_nullable_error),
        ("pipeDelimited", False, {}, 200, []),
    ],
)
def test_integer_array_non_nullable_items(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[
            List[int], QueryParam(style=style, explode=explode)
        ],  # type: ignore[arg-type]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        ("form", True, {"param": "1"}, 200, [1]),
        (
            "form",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        ("form", True, {"param": "1,2"}, 422, array_not_a_valid_integer_error),
        ("form", True, {"param": ""}, 200, [None]),
        ("form", True, [("param", ""), ("param", "")], 200, [None, None]),
        ("form", True, {}, 200, []),
        # form, False
        ("form", False, {"param": "1"}, 200, [1]),
        (
            "form",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        ("form", False, {"param": "1,2"}, 200, [1, 2]),
        ("form", False, {"param": ""}, 200, [None]),
        ("form", False, {}, 200, []),
        # spaceDelimited, True
        ("spaceDelimited", True, {"param": "1"}, 200, [1]),
        (
            "spaceDelimited",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1 2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "spaceDelimited",
            True,
            {"param": "1|2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", True, {"param": ""}, 200, [None]),
        ("spaceDelimited", True, [("param", ""), ("param", "")], 200, [None, None]),
        ("spaceDelimited", True, {}, 200, []),
        # spaceDelimited, False
        ("spaceDelimited", False, {"param": "1"}, 200, [1]),
        (
            "spaceDelimited",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        (
            "spaceDelimited",
            False,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", False, {"param": "1 2"}, 200, [1, 2]),
        (
            "spaceDelimited",
            False,
            {"param": "1|2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("spaceDelimited", False, {"param": ""}, 200, [None]),
        ("spaceDelimited", False, {}, 200, []),
        # pipeDelimited, True
        ("pipeDelimited", True, {"param": "1"}, 200, [1]),
        (
            "pipeDelimited",
            True,
            [("param", "1"), ("param", "2")],
            200,
            [1, 2],
        ),
        ("pipeDelimited", True, {"param": "1,2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": "1 2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": "1|2"}, 422, array_not_a_valid_integer_error),
        ("pipeDelimited", True, {"param": ""}, 200, [None]),
        ("pipeDelimited", True, [("param", ""), ("param", "")], 200, [None, None]),
        ("pipeDelimited", True, {}, 200, []),
        # pipeDelimited, False
        ("pipeDelimited", False, {"param": "1"}, 200, [1]),
        (
            "pipeDelimited",
            False,
            [("param", "1"), ("param", "2")],
            422,
            invalid_serialization_error,
        ),
        (
            "pipeDelimited",
            False,
            {"param": "1,2"},
            422,
            array_not_a_valid_integer_error,
        ),
        (
            "pipeDelimited",
            False,
            {"param": "1 2"},
            422,
            array_not_a_valid_integer_error,
        ),
        ("pipeDelimited", False, {"param": "1|2"}, 200, [1, 2]),
        ("pipeDelimited", False, {"param": ""}, 200, [None]),
        ("pipeDelimited", False, {}, 200, []),
    ],
)
def test_integer_array_nullable_items(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
):
    async def endpoint(
        param: Annotated[
            List[Optional[int]], QueryParam(style=style, explode=explode)
        ],  # type: ignore[arg-type]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


@pytest.mark.parametrize(
    "style,explode,params,status_code,expected_json_response",
    [
        # form, True
        (
            "form",
            True,
            {"foo": "1", "bar": "2"},
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "form",
            True,
            {"foo": "1", "bar": "2", "baz": "4"},
            200,
            {"foo": "1", "bar": 2, "baz": "4"},
        ),
        (
            "form",
            True,
            {"foo": "1"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "form",
            True,
            {"bar": "2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "form",
            True,
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
        (
            "form",
            True,
            {"foo": "1", "bar": "notanumber"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        # form, False
        (
            "form",
            False,
            {"param": "foo,1,bar,2"},
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "form",
            False,
            {"param": "foo,1,bar,2,baz,4"},
            200,
            {"foo": "1", "bar": 2, "baz": "4"},
        ),
        (
            "form",
            False,
            {"param": "foo,1"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "form",
            False,
            {"param": "bar,2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "form",
            False,
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param"],
                        "msg": "Missing required query parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        (
            "form",
            False,
            {"param": "foo,1,bar,123notanumber"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
        (
            "form",
            False,
            {"param": ""},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    },
                ]
            },
        ),
        # deepObject, True
        (
            "deepObject",
            True,
            {"param[foo]": "1", "param[bar]": "2"},
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "deepObject",
            True,
            {"param[foo]": "1", "param[bar]": "2", "otherparam": "123"},
            200,
            {"foo": "1", "bar": 2, "baz": "3"},
        ),
        (
            "deepObject",
            True,
            {"param[foo]": "1", "param[bar]": "2", "param[baz]": "4"},
            200,
            {"foo": "1", "bar": 2, "baz": "4"},
        ),
        (
            "deepObject",
            True,
            {"param[foo]": "1"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "deepObject",
            True,
            {"param[bar]": "2"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "foo"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        (
            "deepObject",
            True,
            {},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param"],
                        "msg": "Missing required query parameter",
                        "type": "value_error",
                    }
                ]
            },
        ),
        (
            "deepObject",
            True,
            {"param[foo]": "1", "param[bar]": "notanumber"},
            422,
            {
                "detail": [
                    {
                        "loc": ["query", "param", "bar"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    }
                ]
            },
        ),
    ],
)
def test_object(
    style: QueryParamStyles,
    explode: bool,
    params: Dict[str, Any],
    status_code: int,
    expected_json_response: Dict[str, Any],
) -> None:
    class Model(BaseModel):
        foo: str
        bar: int
        baz: Optional[str] = "3"

    async def endpoint(
        param: Annotated[
            Model, QueryParam(style=style, explode=explode)
        ],  # type: ignore[arg-type]
    ) -> Any:
        return param

    app = App([Path("/", get=endpoint)])

    client = TestClient(app)

    response = client.get("/", params=params)
    assert response.status_code == status_code
    assert response.json() == expected_json_response


def test_deepObject_not_explode_is_not_allowed() -> None:
    async def endpoint(
        param: Annotated[str, QueryParam(style="deepObject", explode=False)]
    ) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", get=endpoint)])

    with pytest.raises(
        ValueError, match="deepObject can only be used with explode=True"
    ):
        with TestClient(app):
            pass  # pragma: no cover


def test_parameter_is_used_in_multiple_locations() -> None:
    async def dep(param: FromQuery[str]) -> None:
        ...

    async def endpoint(param: FromQuery[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint, dependencies=[Depends(dep)]))])

    client = TestClient(app)

    resp = client.get("/", params={"param": "foo"})
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

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_multiple_parameters() -> None:
    async def endpoint(param1: FromQuery[str], param2: FromQuery[str]) -> None:
        ...

    app = App([Path("/", get=Operation(endpoint))])

    client = TestClient(app)

    resp = client.get("/", params={"param1": "foo", "param2": "bar"})
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
                            "in": "query",
                        },
                        {
                            "required": True,
                            "style": "form",
                            "explode": True,
                            "schema": {"title": "Param2", "type": "string"},
                            "name": "param2",
                            "in": "query",
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
