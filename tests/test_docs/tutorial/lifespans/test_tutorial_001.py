from docs_src.tutorial.lifespans.tutorial_001 import app
from xpresso.testclient import TestClient


def test_lifespan() -> None:

    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200, resp.content

    assert resp.json() == {"app_id": id(app)}
