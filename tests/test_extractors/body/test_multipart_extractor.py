import json
import sys
import typing
from io import BytesIO

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import (
    App,
    ExtractField,
    ExtractRepeatedField,
    FormEncodedField,
    FromFile,
    FromFormField,
    FromJson,
    FromMultipart,
    Multipart,
    Path,
    UploadFile,
)

Files = typing.List[
    typing.Tuple[
        str,
        typing.Union[
            typing.Tuple[
                typing.Optional[str], typing.Union[bytes, typing.BinaryIO], str
            ],
            typing.Tuple[typing.Optional[str], typing.Union[bytes, typing.BinaryIO]],
        ],
    ]
]
Data = typing.List[typing.Tuple[str, str]]


class TruthyEmptyList(typing.List[typing.Any]):
    """Used to force multipart requests"""

    def __bool__(self) -> bool:
        return True


class ScalarModel(BaseModel):
    a: int
    b: str


class JsonModel(BaseModel):
    inner: ScalarModel


def test_json_from_file() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_file: ExtractField[FromJson[JsonModel]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.json_file.dict() == json_model_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "json_file",
            (
                "file.json",
                BytesIO(json.dumps(json_model_payload).encode()),
                "application/json",
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_json_from_form_data() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_data: ExtractField[FromJson[JsonModel]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.json_data.dict() == json_model_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = TruthyEmptyList()
    data: Data = [("json_data", json.dumps(json_model_payload))]

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_json_from_form_field() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_file: ExtractField[FromJson[JsonModel]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.json_file.dict() == json_model_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = TruthyEmptyList()
    data: Data = [("json_file", json.dumps(json_model_payload))]

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_array_of_json_from_repeated_field() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}
    json_model_payload = {"inner": scalar_model_payload}

    class FormDataModel(BaseModel):
        json_file: ExtractRepeatedField[FromJson[typing.List[JsonModel]]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert [body.json_file[0].dict(), body.json_file[1].dict()] == [
            json_model_payload,
            json_model_payload,
        ]
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "json_file",
            (
                None,
                json.dumps(json_model_payload).encode(),
                "application/json",
            ),
        ),
        (
            "json_file",
            (
                None,
                json.dumps(json_model_payload).encode(),
                "application/json",
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_uploadfile() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: ExtractField[FromFile[UploadFile]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert (await body.file.read()) == file_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "file",
            (
                "file.txt",
                BytesIO(file_payload),
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_array_of_uploadfile() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: ExtractRepeatedField[FromFile[typing.List[UploadFile]]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert [await body.file[0].read(), await body.file[1].read()] == [
            file_payload,
            file_payload,
        ]
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "file",
            (
                "file1.txt",
                file_payload,
            ),
        ),
        (
            "file",
            (
                "file2.txt",
                file_payload,
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_bytes() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: ExtractField[FromFile[bytes]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.file == file_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "file",
            (
                "file.txt",
                BytesIO(file_payload),
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_array_of_bytes() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: ExtractRepeatedField[FromFile[typing.List[bytes]]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert [body.file[0], body.file[1]] == [
            file_payload,
            file_payload,
        ]
        return Response()

    app = App([Path("/", post=test)])

    files: Files = [
        (
            "file",
            (
                "file1.txt",
                file_payload,
            ),
        ),
        (
            "file",
            (
                "file2.txt",
                file_payload,
            ),
        ),
    ]
    data: Data = []

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_form_field_object() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}

    class FormDataModel(BaseModel):
        form_object: FromFormField[ScalarModel]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.form_object.dict() == scalar_model_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = TruthyEmptyList()
    data: Data = [("a", "1"), ("b", "2")]

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_form_field_deep_object() -> None:

    scalar_model_payload = {"a": 1, "b": "2"}

    class FormDataModel(BaseModel):
        form_deep_object: Annotated[ScalarModel, FormEncodedField(style="deepObject")]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.form_deep_object.dict() == scalar_model_payload
        return Response()

    app = App([Path("/", post=test)])

    files: Files = TruthyEmptyList()
    data: Data = [
        ("form_deep_object[a]", "1"),
        ("form_deep_object[b]", "2"),
    ]

    with TestClient(app) as client:
        resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text


def test_dissallow_mismatched_media_type():
    class FormDataModel(BaseModel):
        field: FromFormField[str]

    async def test(
        body: Annotated[
            FormDataModel,
            Multipart(enforce_media_type=True),  # True is the default
        ]
    ) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    data: Data = [
        ("field", "1234"),
    ]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 415, resp.text
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "headers", "content-type"],
                "msg": "Media type application/x-www-form-urlencoded is not supported",
                "type": "value_error",
            }
        ]
    }


def test_allow_mismatched_media_type():
    class FormDataModel(BaseModel):
        field: FromFormField[str]

    async def test(
        body: Annotated[FormDataModel, Multipart(enforce_media_type=False)]
    ) -> Response:
        return Response()

    app = App([Path("/", post=test)])

    data: Data = [
        ("field", "1234"),
    ]

    with TestClient(app) as client:
        resp = client.post("/", data=data)
    assert resp.status_code == 200, resp.text
