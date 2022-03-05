from pydantic import BaseModel

from xpresso import App, Depends, Path, Security
from xpresso.security import APIKeyHeader
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

apikey = APIKeyHeader(scheme_name="apikey", param_name="key")


class User(BaseModel):
    username: str


def get_current_user(key: Annotated[str, Security(apikey)]):
    user = User(username=key)
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
        overrides[apikey] = lambda: "secret"

        client = TestClient(app)

        response = client.get("/users/me")
        assert response.status_code == 200, response.text
        assert response.json() == {"username": "secret"}
