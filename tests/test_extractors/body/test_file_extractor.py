from typing import Dict, Optional

import pytest
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, File, FromFile, Path, Request, UploadFile
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
                    "loc": ["headers", "content-type"],
                    "msg": err,
                    "type": "value_error",
                }
            ]
        }


def test_consume() -> None:
    async def test(
        body: Annotated[bytes, File(consume=False)], request: Request
    ) -> None:
        assert body == await request.body()

    app = App([Path("/", post=test)])

    with TestClient(app) as client:
        resp = client.post("/", json="test")
    assert resp.status_code == 200
