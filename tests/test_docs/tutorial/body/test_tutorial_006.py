from docs_src.tutorial.body.tutorial_006 import app
from xpresso.testclient import TestClient

client = TestClient(app)


def test_body_tutorial_006():
    response = client.post("/webhook", json={"foo": "bar"})
    assert response.status_code == 200, response.content
    assert response.json() is True
