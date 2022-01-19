from docs_src.advanced.dependencies.tutorial_003 import app
from xpresso.testclient import TestClient


def test_shared() -> None:
    client = TestClient(app)
    resp = client.get("/shared")
    assert resp.status_code == 200, resp.content
