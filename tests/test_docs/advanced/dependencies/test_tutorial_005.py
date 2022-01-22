from uuid import UUID, uuid4

from docs_src.advanced.dependencies.tutorial_005 import app
from xpresso.testclient import TestClient


def test_context_id() -> None:
    client = TestClient(app)

    resp = client.get("/items/foo")
    assert resp.status_code == 200, resp.content
    UUID(resp.headers["X-Request-Context"])  # just a valid UUID

    ctx = str(uuid4())
    resp = client.get("/items/foo", headers={"X-Request-Context": ctx})
    assert resp.headers["X-Request-Context"] == ctx
