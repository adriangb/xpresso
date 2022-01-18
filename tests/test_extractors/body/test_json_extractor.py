import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from pydantic import BaseModel
from starlette.testclient import TestClient

from xpresso import App, FromJson, Json, Path, Response


class InnerModel(BaseModel):
    a: int
    b: str


class OuterModel(BaseModel):
    inner: InnerModel


inner_payload = {"a": 1, "b": "2"}
outer_payload = {"inner": inner_payload}


def test_explicit_pydantic_json_body() -> None:
    async def test(model: FromJson[OuterModel]) -> Response:
        assert model.dict() == outer_payload
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", json=outer_payload)
    assert resp.status_code == 200


def test_explicit_builtin_array_of_objects() -> None:
    async def test(outer_list: FromJson[typing.List[OuterModel]]) -> Response:
        assert all(item.dict() == outer_payload for item in outer_list)
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", json=[outer_payload, outer_payload])
    assert resp.status_code == 200


def test_explicit_builtin_scalar() -> None:
    async def test(value: FromJson[int]) -> Response:
        assert value == 1
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", json=1)
    assert resp.status_code == 200


def test_media_type_validation_enabled() -> None:
    async def endpoint(
        value: Annotated[int, Json(enforce_media_type=True)]
    ) -> Response:
        assert value == 1
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"1", headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        resp = client.post("/", data=b"1", headers={"Content-Type": "text/plain"})
        assert resp.status_code == 415
        assert "Media type text/plain is not supported" in resp.text


def test_media_type_validation_disabled() -> None:
    async def test(value: Annotated[int, Json(enforce_media_type=False)]) -> Response:
        assert value == 1
        return Response()

    app = App([Path("/validate-false", post=test)])

    with TestClient(app) as client:
        resp = client.post(
            "/validate-false", data=b"1", headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200
        resp = client.post(
            "/validate-false", data=b"1", headers={"Content-Type": "text/plain"}
        )
        assert resp.status_code == 200


def test_empty_body_no_default() -> None:
    async def test(model: FromJson[OuterModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"", headers={"content-type": "application/json"})
    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {"loc": ["body"], "msg": "Missing required value", "type": "value_error"}
        ]
    }


def test_empty_body_with_default() -> None:
    default = OuterModel(inner=InnerModel(a=1, b="2"))

    async def test(model: FromJson[OuterModel] = default) -> OuterModel:
        return model

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"", headers={"content-type": "application/json"})
    assert resp.status_code == 200
    assert resp.json() == default.dict()


def test_invalid_json() -> None:
    async def test(model: FromJson[OuterModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post(
            "/", data=b"notvalidjson", headers={"content-type": "application/json"}
        )
    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {"loc": ["body"], "msg": "Data is not valid JSON", "type": "type_error"}
        ]
    }


def test_nullable() -> None:
    async def test(model: FromJson[typing.Optional[OuterModel]]) -> None:
        assert model is None

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post(
            "/", data=b"null", headers={"content-type": "application/json"}
        )
    assert resp.status_code == 200
