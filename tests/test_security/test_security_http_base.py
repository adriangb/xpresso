from typing import Any, Dict, Generator

import pytest

from xpresso import App, Path, Security
from xpresso.security import HTTPAuthorizationCredentials, HTTPBase
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

security = HTTPBase(scheme="Other")


def read_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)]
):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials}


app = App([Path("/users/me", get=read_current_user)])


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/users/me": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                    }
                },
                "security": [{"HTTPBase": []}],
            }
        }
    },
    "components": {
        "securitySchemes": {"HTTPBase": {"type": "http", "scheme": "Other"}}
    },
}


def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_security_http_base(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Other foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"scheme": "Other", "credentials": "foobar"}


def test_security_http_base_no_credentials(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}
