from xpresso import App, Depends, Path
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


def test_override_with_marker() -> None:
    def dep() -> int:
        ...

    async def endpoint(v: Annotated[int, Depends(dep)]) -> int:
        return v

    app = App([Path("/", get=endpoint)])

    app.dependency_overrides[dep] = lambda: 2

    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200, resp.content
    assert resp.json() == 2
