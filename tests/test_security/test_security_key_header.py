from pydantic import BaseModel

from xpresso import App, Depends, Path
from xpresso.security import APIKeyHeader
from xpresso.testclient import TestClient
from xpresso.typing import Annotated


class APIKey(APIKeyHeader):
    scheme_name = "apikey"
    name = "key"


class User(BaseModel):
    username: str


def get_current_user(key: APIKey):
    user = User(username=key.api_key)
    return user


def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


app = App([Path("/users/me", get=read_current_user)])


client = TestClient(app)


def test_security_api_key():
    response = client.get("/users/me", headers={"key": "secret"})
    assert response.status_code == 200, response.text
    assert response.json() == {"username": "secret"}


def test_security_api_key_no_key():
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_dependency_override():
    with app.dependency_overrides as overrides:
        overrides[APIKey] = lambda: APIKey("secret")

        client = TestClient(app)

        response = client.get("/users/me")
        assert response.status_code == 200, response.text
        assert response.json() == {"username": "secret"}
