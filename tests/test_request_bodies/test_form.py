"""Tests for forms and form encoded form fields

The actual parsing of url encoded form fields is shared with query parameters
and is extensively tested there, and thus not repeated here.
"""
import typing

import pytest
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import FormField, FromFormData, FromFormField, Path
from xpresso.applications import App
from xpresso.typing import Annotated


def test_form_field() -> None:
    class FormModel(BaseModel):
        field: FromFormField[int]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/", data={"field": "2"})
    assert resp.status_code == 200, resp.content

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
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
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "required": ["field"],
                                    "type": "object",
                                    "properties": {
                                        "field": {
                                            "title": "Field",
                                            "type": "integer",
                                        }
                                    },
                                },
                                "encoding": {
                                    "field": {"style": "form", "explode": True}
                                },
                            }
                        },
                        "required": True,
                    },
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
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_form_field_alias() -> None:
    class FormModel(BaseModel):
        field: Annotated[int, FormField(alias="realFieldName")]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/", data={"realFieldName": "2"})
    assert resp.status_code == 200, resp.content

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
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
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "required": ["realFieldName"],
                                    "type": "object",
                                    "properties": {
                                        "realFieldName": {
                                            "title": "Realfieldname",
                                            "type": "integer",
                                        }
                                    },
                                },
                                "encoding": {
                                    "realFieldName": {"style": "form", "explode": True}
                                },
                            }
                        },
                        "required": True,
                    },
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
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_invalid_serialization() -> None:
    class FormModel(BaseModel):
        field: Annotated[typing.List[int], FormField(explode=False)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    # use explode=True encoding when explode=False was expected
    resp = client.post("/", data=[("field", "1"), ("field", "2")])
    assert resp.status_code == 422, resp.content
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "field"],
                "msg": "Data is not a valid URL encoded form",
                "type": "type_error",
            }
        ]
    }


@pytest.mark.parametrize(
    "data,status_code,json_response",
    [
        ({"field": "123"}, 200, {"field": "123"}),
        (None, 200, None),
    ],
)
def test_optional_form(
    data: typing.Optional[typing.Iterable[typing.Tuple[str, str]]],
    status_code: int,
    json_response: typing.Dict[str, typing.Any],
) -> None:
    class FormModel(BaseModel):
        field: str

    async def test(
        body: FromFormData[typing.Optional[FormModel]] = None,
    ) -> typing.Any:
        return body

    app = App([Path("/", post=test)])
    client = TestClient(app)

    resp = client.post(
        "/",
        data=data,
    )
    assert resp.status_code == status_code, resp.text
    assert resp.json() == json_response
