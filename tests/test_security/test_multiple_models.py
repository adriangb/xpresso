from typing import Generator, Optional

import pytest
from pydantic import BaseModel

from xpresso import App, Depends, Path
from xpresso.security import (
    AlternativeSecuritySchemes,
    APIKeyHeader,
    OAuth2AuthorizationCodeBearer,
    RequiredSecuritySchemes,
)
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


class APIKey1(APIKeyHeader):
    scheme_name = "apikey1"
    name = "key1"


class APIKey2(APIKeyHeader):
    scheme_name = "apikey2"
    name = "key2"


class APIKeys(RequiredSecuritySchemes):
    key1: APIKey1
    key2: APIKey2


class OAuth2(OAuth2AuthorizationCodeBearer):
    scheme_name = "oauth2"
    authorization_url = "authorize"
    token_url = "token"
    scopes = {"read": "read things", "write": "write things"}


class OAuth2WithScopes(OAuth2):
    required_scopes = {"read"}


class SecurityModel(AlternativeSecuritySchemes):
    apikeys: Optional[APIKeys]
    oauth: Optional[OAuth2WithScopes]


class User(BaseModel):
    username: str


def get_current_user(auth: SecurityModel):
    if auth.apikeys is not None:
        assert auth.apikeys.key2.api_key
        return User(username=auth.apikeys.key1.api_key)
    if auth.oauth is not None:
        assert auth.oauth.required_scopes  # or something with the token
        return User(username=auth.oauth.token)


def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


app = App([Path("/users/me", get=read_current_user)])


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def test_security_api_key_both_keys(client: TestClient):
    response = client.get("/users/me", headers={"key1": "secret", "key2": "foobarbaz"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "secret"}


def test_security_api_key_missing_one_key(client: TestClient):
    response = client.get("/users/me", headers={"key1": "secret"})
    assert response.status_code == 401, response.text


def test_security_api_key_no_key(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_no_auth(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token(client: TestClient):
    response = client.get(
        "/users/me", headers={"Authorization": "Non-existent testtoken"}
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token_with_api_keys(client: TestClient):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer testtoken",
            "key1": "secret",
            "key2": "foobarbaz",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "secret"}


def test_token(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "testtoken"}