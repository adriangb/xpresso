from typing import Any, Dict

from xpresso import App, Path, Security
from xpresso.security import APIKeyHeader
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


def test_duplicate_scheme_name_resolution() -> None:

    api_key1 = APIKeyHeader(name="key1")
    api_key2 = APIKeyHeader(name="key2")

    def endpoint(
        key1: Annotated[str, Security(api_key1)],
        key2: Annotated[str, Security(api_key2)],
    ) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    openapi_schema: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {"200": {"description": "Successful Response"}},
                    "security": [{"APIKeyHeader_1": []}, {"APIKeyHeader_2": []}],
                }
            }
        },
        "components": {
            "securitySchemes": {
                "APIKeyHeader_1": {"type": "apiKey", "name": "key1", "in": "header"},
                "APIKeyHeader_2": {"type": "apiKey", "name": "key2", "in": "header"},
            }
        },
    }

    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema, response.json()


def test_scheme_name() -> None:
    api_key = APIKeyHeader(name="key1")

    def endpoint(
        key: Annotated[str, Security(api_key, scheme_name="foobarbaz")],
    ) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    openapi_schema: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {"200": {"description": "Successful Response"}},
                    "security": [{"foobarbaz": []}],
                }
            }
        },
        "components": {
            "securitySchemes": {
                "foobarbaz": {"type": "apiKey", "name": "key1", "in": "header"}
            }
        },
    }

    client = TestClient(app)

    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema
