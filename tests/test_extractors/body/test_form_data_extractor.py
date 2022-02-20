import json
import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import (
    ExtractField,
    ExtractRepeatedField,
    Form,
    FormEncodedField,
    FormField,
    FromFormData,
    FromFormField,
    FromJson,
    Path,
    RepeatedFormField,
)
from xpresso.applications import App

Data = typing.List[typing.Tuple[str, str]]


class TruthyEmptyList(typing.List[typing.Any]):
    def __bool__(self) -> bool:
        return True


class ScalarModel(BaseModel):
    a: int
    b: str


class JsonModel(BaseModel):
    inner: ScalarModel


def test_json_from_form_field() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_field: ExtractField[FromJson[JsonModel]]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.json_field.dict() == json_model_payload
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [("json_field", json.dumps(json_model_payload))]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_json_list_not_repeated() -> None:
    class FormDataModel(BaseModel):
        json_field: ExtractField[FromJson[typing.List[int]]]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.json_field == [1, 2]
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [("json_field", "[1,2]")]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_array_of_json_from_repeated_form_field() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_field: ExtractRepeatedField[FromJson[typing.List[JsonModel]]]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert [body.json_field[0].dict(), body.json_field[1].dict()] == [
            json_model_payload,
            json_model_payload,
        ]
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [
        ("json_field", json.dumps(json_model_payload)),
        ("json_field", json.dumps(json_model_payload)),
    ]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_form_field_object() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}

    class FormDataModel(BaseModel):
        form_object: FromFormField[ScalarModel]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.form_object.dict() == scalar_model_payload
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [("a", "1"), ("b", "2")]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_form_field_deep_object() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}

    class FormDataModel(BaseModel):
        form_deep_object: Annotated[ScalarModel, FormEncodedField(style="deepObject")]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.form_deep_object.dict() == scalar_model_payload
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [
        ("form_deep_object[a]", "1"),
        ("form_deep_object[b]", "2"),
    ]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_json_from_form_field_with_alias() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_field: Annotated[FromJson[JsonModel], FormField(alias="readlFieldName")]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.json_field.dict() == json_model_payload
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [("readlFieldName", json.dumps(json_model_payload))]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_json_list_not_repeated_with_alias() -> None:
    class FormDataModel(BaseModel):
        json_field: Annotated[
            FromJson[typing.List[int]], FormField(alias="realFieldName")
        ]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert body.json_field == [1, 2]
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [("realFieldName", "[1,2]")]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_array_of_json_from_repeated_form_field_with_alias() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_field: Annotated[
            FromJson[typing.List[JsonModel]], RepeatedFormField(alias="realFieldName")
        ]

    async def test(body: FromFormData[FormDataModel]) -> Response:
        assert [body.json_field[0].dict(), body.json_field[1].dict()] == [
            json_model_payload,
            json_model_payload,
        ]
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [
        ("realFieldName", json.dumps(json_model_payload)),
        ("realFieldName", json.dumps(json_model_payload)),
    ]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text


def test_dissallow_mismatched_media_type():
    class FormDataModel(BaseModel):
        field: FromFormField[str]

    async def test(
        body: Annotated[
            FormDataModel,
            Form(enforce_media_type=True),  # True is the default
        ]
    ) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    data: Data = [
        ("field", "1234"),
    ]
    files = TruthyEmptyList()

    with TestClient(app) as client:
        resp = client.post("/", data=data, files=files)
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "headers", "content-type"],
                "msg": "Media type multipart/form-data is not supported",
                "type": "value_error",
            }
        ]
    }


def test_allow_mismatched_media_type():
    class FormDataModel(BaseModel):
        field: FromFormField[str]

    async def test(
        body: Annotated[FormDataModel, Form(enforce_media_type=False)]
    ) -> Response:
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [
        ("field", "1234"),
    ]
    files = TruthyEmptyList()

    with TestClient(app) as client:
        resp = client.post("/", data=data, files=files)
    assert resp.status_code == 200, resp.text


@pytest.mark.parametrize(
    "data,status_code,json_response",
    [
        ({"field": "123"}, 200, {"field": "123"}),
        (
            {"notfield": "123"},
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "field"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        ),
        ({}, 200, None),
        (None, 200, None),
    ],
)
def test_optional_form_data(
    data: typing.Optional[Data],
    status_code: int,
    json_response: typing.Dict[str, typing.Any],
) -> None:
    class FormDataModel(BaseModel):
        field: str

    async def test(
        body: FromFormData[typing.Optional[FormDataModel]] = None,
    ) -> typing.Any:
        return body

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post(
            "/",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert resp.status_code == status_code, resp.text
    assert resp.json() == json_response
