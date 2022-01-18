from docs_src.tutorial.di_bind_abstractions import app
from xpresso.testclient import TestClient


def test_delete() -> None:
    client = TestClient(app)
    resp = client.delete("/users/me")
    assert resp.status_code == 200, resp.content
