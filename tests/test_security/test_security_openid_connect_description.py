from typing import Any, Dict, Generator

import pytest
from pydantic import BaseModel

from xpresso import App, Dependant, Path, Security
from xpresso.security import OpenIdConnect
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

oid = OpenIdConnect(
    openIdConnectUrl="/openid", description="OpenIdConnect security scheme"
)


class User(BaseModel):
    username: str


def get_current_user(oauth_header: Annotated[str, Security(oid)]):
    user = User(username=oauth_header)
    return user


def read_current_user(current_user: Annotated[User, Dependant(get_current_user)]):
    return current_user


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
                "security": [{"OpenIdConnect": []}],
            }
        }
    },
    "components": {
        "securitySchemes": {
            "OpenIdConnect": {
                "type": "openIdConnect",
                "openIdConnectUrl": "/openid",
                "description": "OpenIdConnect security scheme",
            }
        }
    },
}


def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_security_oauth2(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Bearer footokenbar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "Bearer footokenbar"}


def test_security_oauth2_password_other_header(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Other footokenbar"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "Other footokenbar"}


def test_security_oauth2_password_bearer_no_header(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}
