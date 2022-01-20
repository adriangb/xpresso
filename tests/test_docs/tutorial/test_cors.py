import os
from unittest.mock import patch

from docs_src.tutorial.cors import create_app
from xpresso.testclient import TestClient


def test_cors_middleware() -> None:
    with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": '["https://example.com"]'}):
        app = create_app()

    client = TestClient(app)

    # Test pre-flight response
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Example",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200, response.text
    assert response.text == "OK"
    assert response.headers["access-control-allow-origin"] == "https://example.com"
    assert response.headers["access-control-allow-headers"] == "X-Example"

    # Test standard response
    headers = {"Origin": "https://example.com"}
    response = client.get("/", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello World"}
    assert response.headers["access-control-allow-origin"] == "https://example.com"

    # Test non-CORS response
    response = client.get("/")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Hello World"}
    assert "access-control-allow-origin" not in response.headers
