from dataclasses import dataclass
from typing import Any, Dict

from docs_src.tutorial.di_app_scoped import Config, app
from xpresso.dependencies.models import Dependant
from xpresso.testclient import TestClient


def test_dep_is_only_loaded_once():
    calls = 0

    @dataclass
    class ConfigProbe(Config):
        host: str = "http://example.com"

        def __post_init__(self) -> None:
            nonlocal calls
            calls += 1

    with app.container.bind(Dependant(lambda: ConfigProbe(), scope="app"), Config):
        with TestClient(app) as client:
            resp = client.get("/")
            assert resp.json() == "Hello from http://example.com!"
            resp = client.get("/")
            assert resp.json() == "Hello from http://example.com!"
    assert calls == 1


openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response", "type": "string"}
                            }
                        },
                    }
                }
            }
        }
    },
}


def test_openapi_schema():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200, response.content
        assert response.json() == openapi_schema
