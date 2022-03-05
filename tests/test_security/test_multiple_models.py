from typing import Union

from pydantic import BaseModel

from xpresso import App, Depends, Path
from xpresso.security import (
    APIKeyHeader,
    OAuth2AuthorizationCodeBearer,
    OAuth2Token,
    Security,
    SecurityModel,
)
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


class APIKey1(APIKeyHeader):
    scheme_name = "apikey1"
    name = "key1"


apikey1 = APIKeyHeader(param_name="key1", scheme_name="apikey1")
apikey2 = APIKeyHeader(param_name="key2", scheme_name="apikey2")
oauth2 = OAuth2AuthorizationCodeBearer(
    token_url="token",
    authorization_url="authorize",
    scheme_name="oauth",
    scopes={"read": "read things", "write": "write things"},
)


class APIKeys(SecurityModel):
    key1: Annotated[str, Security(apikey1)]
    key2: Annotated[str, Security(apikey2)]


class OAuth2(SecurityModel):
    token: Annotated[OAuth2Token, Security(oauth2.require_scopes("read"))]


class User(BaseModel):
    username: str


def get_current_user(auth: Annotated[Union[APIKeys, OAuth2], Security()]):
    if isinstance(auth, APIKeys):
        assert auth.key1 == "secret"
        return User(username=auth.key2)
    assert auth.token.required_scopes  # or something with the token
    return User(username=auth.token.token)


def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


app = App([Path("/users/me", get=read_current_user)])


client = TestClient(app)


def test_security_api_key_both_keys():
    response = client.get("/users/me", headers={"key1": "secret", "key2": "foobarbaz"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "foobarbaz"}


def test_security_api_key_missing_one_key():
    response = client.get("/users/me", headers={"key1": "secret"})
    assert response.status_code == 401, response.text


def test_security_api_key_no_key():
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_no_auth():
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token():
    response = client.get(
        "/users/me", headers={"Authorization": "Non-existent testtoken"}
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token_with_api_keys():
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer testtoken",
            "key1": "secret",
            "key2": "foobarbaz",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "foobarbaz"}


def test_valid_token_without_api_keys():
    response = client.get("/users/me", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "testtoken"}
