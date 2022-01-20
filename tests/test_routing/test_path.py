import pytest

from xpresso import App, Path, Request
from xpresso.testclient import TestClient


@pytest.mark.parametrize("path", ["foo", "", "foo/"])
def test_path_item_invalid_path(path: str) -> None:
    with pytest.raises(ValueError, match="must start with '/'"):
        Path("test")
    with pytest.raises(ValueError, match="must start with '/'"):
        Path("")


@pytest.mark.parametrize(
    "method",
    [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "connect",
        "options",
        "trace",
    ],
)
def test_methods(method: str) -> None:
    async def endpoint(request: Request) -> None:
        assert request.method.lower() == method

    app = App([Path("/", **{method: endpoint})])  # type: ignore[arg-type]
    client = TestClient(app)
    resp = client.request(method=method, url="/")
    assert resp.status_code == 200, resp.content
