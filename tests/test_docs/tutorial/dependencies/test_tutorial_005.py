from docs_src.tutorial.dependencies.tutorial_005 import app
from xpresso.testclient import TestClient


def test_echo_user():
    client = TestClient(app)
    response = client.get("/echo/user", params={"username": "foobarbaz"})
    assert response.status_code == 200, response.content
    assert response.json() == {"username": "foobarbaz"}
