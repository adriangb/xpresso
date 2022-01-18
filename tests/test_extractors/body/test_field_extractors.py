import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from di import Dependant
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import ExtractField, FormField, FromFormData, FromJson, Json
from xpresso.applications import App
from xpresso.routing import Path

Data = typing.List[typing.Tuple[str, str]]


def test_non_field_markers_are_ignored() -> None:
    class RandomMarker(Dependant[typing.Any]):
        pass

    class FormDataModel(BaseModel):
        # RandomMarker should be skipped when looking for the field's marker
        field: Annotated[
            str, RandomMarker(), Json(), RandomMarker(), FormField(), RandomMarker()
        ]

    async def test(form: FromFormData[FormDataModel]) -> Response:
        assert form.field == "123"
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data={"field": '"123"'})
    assert resp.status_code == 200, resp.text


def test_field_not_in_form() -> None:
    class FormDataModel(BaseModel):
        field: ExtractField[FromJson[str]]

    async def test(form: FromFormData[FormDataModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data={"notfield": '"123"'})
    assert resp.status_code == 422, resp.text
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "field"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]
    }


def test_form_field_alias() -> None:
    class FormDataModel(BaseModel):
        field: Annotated[FromJson[str], FormField(alias="notfield")]

    async def test(form: FromFormData[FormDataModel]) -> Response:
        assert form.field == "123"
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data={"notfield": '"123"'})
    assert resp.status_code == 200, resp.text
