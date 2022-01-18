from base64 import b64encode
from typing import Any, Dict, Generator, Optional

import pytest
from requests.auth import HTTPBasicAuth  # type: ignore[import]

from xpresso import App, Path, Security
from xpresso.security import HTTPBasic, HTTPBasicCredentials
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

security = HTTPBasic(auto_error=False)


def read_current_user(
    credentials: Annotated[Optional[HTTPBasicCredentials], Security(security)]
):
    if credentials is None:
        return {"msg": "Create an account first"}
    return {"username": credentials.username, "password": credentials.password}


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
                "security": [{"HTTPBasic": []}],
            }
        }
    },
    "components": {
        "securitySchemes": {"HTTPBasic": {"type": "http", "scheme": "basic"}}
    },
}


def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_security_http_basic(client: TestClient):
    auth = HTTPBasicAuth(username="john", password="secret")
    response = client.get("/users/me", auth=auth)
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "john", "password": "secret"}


def test_security_http_basic_no_credentials(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}


def test_security_http_basic_invalid_credentials(client: TestClient):
    response = client.get(
        "/users/me", headers={"Authorization": "Basic notabase64token"}
    )
    assert response.status_code == 401, response.text
    assert response.headers["WWW-Authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}


def test_security_http_basic_non_basic_credentials(client: TestClient):
    payload = b64encode(b"johnsecret").decode("ascii")
    auth_header = f"Basic {payload}"
    response = client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == 401, response.text
    assert response.headers["WWW-Authenticate"] == "Basic"
    assert response.json() == {"detail": "Invalid authentication credentials"}
