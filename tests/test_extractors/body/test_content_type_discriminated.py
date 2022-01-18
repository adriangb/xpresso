import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest
from starlette.testclient import TestClient

from xpresso import App, ByContentType, File, FromJson, Path, UploadFile


@pytest.mark.parametrize(
    "headers,response",
    [
        ({"content-type": "image/png"}, "image/png"),
        ({"content-type": "image/jpg"}, "image/jpg"),
        ({"content-type": "image/tiff"}, "image/tiff"),
        ({"content-type": "application/json"}, "application/json"),
    ],
)
def test_multiple_content_types(headers: typing.Dict[str, typing.Any], response: str):
    async def endpoint(
        body: ByContentType[
            typing.Union[
                Annotated[UploadFile, File(media_type="image/png,image/jpg")],
                Annotated[UploadFile, File(media_type="image/*")],
                Annotated[UploadFile, File(media_type="text/plain")],
                FromJson[typing.List[int]],
            ]
        ]
    ) -> str:
        if isinstance(body, UploadFile):
            assert await body.read() == b"[1,2]"
            return body.content_type  # type: ignore[return-value]
        assert body == [1, 2]
        return "application/json"

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)

    resp = client.post("/", data=b"[1,2]", headers=headers)
    assert resp.status_code == 200, resp.content
    assert resp.json() == response
