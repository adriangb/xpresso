from docs_src.tutorial.lifespans.tutorial_002 import app
from xpresso.testclient import TestClient


def test_lifespan() -> None:

    with TestClient(app) as client:
        resp = client.get("/logs")
    assert resp.status_code == 200, resp.content
    assert set(resp.json()) == {"App lifespan", "Router lifespan"}
