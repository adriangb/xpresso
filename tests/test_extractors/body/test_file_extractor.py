from dataclasses import dataclass
from typing import Dict, Optional

import pytest
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, ExtractField, File, FromFile, FromFormData, Path, UploadFile
from xpresso.typing import Annotated


def test_bytes_file():
    async def test(file: FromFile[bytes]) -> Response:
        assert file == b"data"
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"data")
    assert resp.status_code == 200


def test_uploadfile_file():
    async def test(file: FromFile[UploadFile]) -> Response:
        assert await file.read() == b"data"
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"data")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "value",
    [
        None,
        b"",
    ],
)
def test_bytes_empty_file(
    value: Optional[bytes],
):
    async def test(file: FromFile[Optional[bytes]] = None) -> Response:
        assert file == b""
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=value)
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "value",
    [
        None,
        b"",
    ],
)
def test_uploadfile_empty_file(
    value: Optional[bytes],
):
    async def test(file: FromFile[UploadFile]) -> Response:
        assert await file.read() == b""
        return Response()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data=value)
    assert resp.status_code == 200


def test_file_cannot_come_from_form_data_bytes():
    # This is really a limitation of files:
    # 1. We don't know the encoding
    # 2. If we did, encoding it back into bytes would make not sense, users should not do this
    # The only way this can happen is if someone tries to extract a file from form data
    # so we use form data to test here, even if the issue is technically unrelated to form data

    @dataclass(frozen=True)
    class FormDataModel:
        file: ExtractField[FromFile[bytes]]

    async def test(form: FromFormData[FormDataModel]) -> None:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", data={"file": "this can't be a file!"})
        assert resp.status_code == 422, resp.content
        assert resp.json() == {
            "detail": [
                {
                    "loc": ["body", "file"],
                    "msg": "Expected a file, got a string",
                    "type": "type_error",
                }
            ]
        }


@pytest.mark.parametrize(
    "file_media_type,enforce,headers,err",
    [
        (None, True, {}, None),
        (None, False, {}, None),
        ("text/plain", True, {}, "Media type missing in content-type header"),
        ("text/plain", False, {}, None),
        ("text/plain", True, {"content-type": "text/plain"}, None),
        ("text/plain", False, {"content-type": "text/plain"}, None),
        ("text/*", True, {"content-type": "text/plain"}, None),
        ("text/*", False, {"content-type": "text/plain"}, None),
        (
            "image/*",
            True,
            {"content-type": "text/plain"},
            "Media type text/plain is not supported",
        ),
        ("image/*", False, {"content-type": "text/plain"}, None),
    ],
)
def test_content_type_validation(
    file_media_type: str,
    enforce: bool,
    headers: Dict[str, str],
    err: Optional[str],
) -> None:
    async def endpoint(
        file: Annotated[
            UploadFile, File(media_type=file_media_type, enforce_media_type=enforce)
        ]
    ) -> Response:
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", data=b"", headers=headers)
    if err is None:
        assert resp.status_code == 200, resp.content
    else:
        assert resp.status_code == 415
        assert resp.json() == {
            "detail": [
                {
                    "loc": ["body", "headers", "content-type"],
                    "msg": err,
                    "type": "value_error",
                }
            ]
        }
