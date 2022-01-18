import sys
from typing import Any, Dict, List, Optional

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from xpresso import App, CookieParam, FromCookie, Path


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
