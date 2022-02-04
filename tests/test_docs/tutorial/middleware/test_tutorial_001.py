from docs_src.tutorial.middleware.tutorial_001 import AppConfig, create_app
from xpresso.testclient import TestClient


def test_cors_middleware() -> None:
    config = AppConfig(cors_origins=["https://frontend.example.com"])

    client = TestClient(create_app(config=config))

    # Test pre-flight response
    headers = {
        "Origin": "https://frontend.example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = client.options("/v1/landing", headers=headers)
    assert response.status_code == 200, response.text
    assert response.text == "OK"
    assert (
        response.headers["access-control-allow-origin"]
        == "https://frontend.example.com"
    )
    assert response.headers["access-control-allow-headers"] == "X-Example"

    # Test standard response
    headers = {"Origin": "https://frontend.example.com"}
    response = client.get("/v1/landing", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello!"}
    assert (
        response.headers["access-control-allow-origin"]
        == "https://frontend.example.com"
    )

    # Test non-CORS response
    response = client.get("/v1/landing")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello!"}
    assert "access-control-allow-origin" not in response.headers
