from docs_src.advanced.dependencies.tutorial_001 import app
from xpresso.testclient import TestClient


def test_get_slow_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/slow")
    assert resp.status_code == 200, resp.content
