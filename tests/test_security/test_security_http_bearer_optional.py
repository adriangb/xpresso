from typing import Any, Dict, Generator, Optional

import pytest

from xpresso import App, Path, Security
from xpresso.security import HTTPAuthorizationCredentials, HTTPBearer
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

security = HTTPBearer(auto_error=False)


def read_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(security)],
):
    if credentials is None:
        return {"msg": "Create an account first"}
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
                "security": [{"HTTPBearer": []}],
            }
        }
    },
    "components": {
        "securitySchemes": {"HTTPBearer": {"type": "http", "scheme": "bearer"}}
    },
}


def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_security_http_bearer(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Bearer foobar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"scheme": "Bearer", "credentials": "foobar"}


def test_security_http_bearer_no_credentials(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}


def test_security_http_bearer_incorrect_scheme_credentials(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Basic notreally"})
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}
