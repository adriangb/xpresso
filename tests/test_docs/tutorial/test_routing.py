from docs_src.tutorial.routing import app
from xpresso.testclient import TestClient


def test_routing() -> None:
    client = TestClient(app)

    resp = client.get("/mount/mount-again/items")
    assert resp.status_code == 200, resp.content
