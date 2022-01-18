import sys
import typing
from dataclasses import dataclass

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Form, FormEncodedField, FromFormData, FromFormField, Path


def test_form_field_scalar_defaults() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: FromFormField[int]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data={"field": "2"})
    assert resp.status_code == 200, resp.content


def test_form_field_scalar_style_form_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[int, FormEncodedField(style="form", explode=True)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data={"field": "2"})
    assert resp.status_code == 200, resp.content


def test_form_field_scalar_style_form_explode_false() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[int, FormEncodedField(style="form", explode=False)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data={"field": "2"})
    assert resp.status_code == 200, resp.content


def test_form_field_array_defaults() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: FromFormField[typing.List[int]]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1"), ("field", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_form_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[typing.List[int], FormEncodedField(explode=True)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1"), ("field", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_form_explode_false() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[typing.List[int], FormEncodedField(explode=False)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1,2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_spaceDelimited_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            typing.List[int], FormEncodedField(style="spaceDelimited", explode=True)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1"), ("field", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_spaceDelimited_explode_false() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            typing.List[int], FormEncodedField(style="spaceDelimited", explode=False)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1 2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_pipeDelimited_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            typing.List[int], FormEncodedField(style="pipeDelimited", explode=True)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1"), ("field", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_array_style_pipeDelimited_explode_false() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            typing.List[int], FormEncodedField(style="pipeDelimited", explode=False)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "1|2")])
    assert resp.status_code == 200, resp.content


class ShallowObject(BaseModel):
    a: int
    b: str


def test_form_field_shallow_object_defaults() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: FromFormField[ShallowObject]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("a", "1"), ("b", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_shallow_object_style_form_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[ShallowObject, FormEncodedField(explode=True)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("a", "1"), ("b", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_shallow_object_style_form_explode_false() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[ShallowObject, FormEncodedField(explode=False)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field", "a,1,b,2")])
    assert resp.status_code == 200, resp.content


def test_form_field_shallow_object_style_deepObject_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            ShallowObject, FormEncodedField(style="deepObject", explode=True)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("field[a]", "1"), ("field[b]", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_deep_object_style_deepObject_explode_true() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            ShallowObject, FormEncodedField(style="deepObject", explode=True)
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post(
            "/",
            data=[
                ("field[a]", "1"),
                ("field[b]", "2"),
            ],
        )
    assert resp.status_code == 200, resp.content


def test_form_field_alias_scalar() -> None:
    class FormModel(BaseModel):
        field: Annotated[int, FormEncodedField(alias="realFieldName")]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == 2
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data={"realFieldName": "2"})
    assert resp.status_code == 200, resp.content


def test_form_field_alias_array() -> None:
    class FormModel(BaseModel):
        field: Annotated[typing.List[int], FormEncodedField(alias="realFieldName")]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=[("realFieldName", "1"), ("realFieldName", "2")])
    assert resp.status_code == 200, resp.content


def test_form_field_alias_deepObject() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[
            ShallowObject, FormEncodedField(style="deepObject", alias="readlFieldName")
        ]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        assert form.field == ShallowObject(a=1, b="2")
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post(
            "/",
            data=[
                ("readlFieldName[a]", "1"),
                ("readlFieldName[b]", "2"),
            ],
        )
    assert resp.status_code == 200, resp.content


def test_invalid_serialization() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: Annotated[ShallowObject, FormEncodedField(explode=False)]

    async def endpoint(form: FromFormData[FormModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        # fields cannot be repeated if explode=False
        # this is just an arbitrary example of a malformed serialzition
        resp = client.post("/", data=[("field", "a,1"), ("field", "b,2")])
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


def test_form_field_from_file() -> None:
    @dataclass(frozen=True)
    class FormModel:
        field: FromFormField[str]

    async def endpoint(
        form: Annotated[FormModel, Form(enforce_media_type=False)]
    ) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", files=[("field", ("file.txt", b"abcd"))])
    assert resp.status_code == 422, resp.content
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "field"],
                "msg": "Expected a string form field but received a file",
                "type": "type_error.unexpectedfilereceived",
            }
        ]
    }
