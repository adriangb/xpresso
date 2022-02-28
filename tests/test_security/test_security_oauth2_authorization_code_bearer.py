from typing import Generator

import pytest

from xpresso import App, Path
from xpresso.security import OAuth2AuthorizationCodeBearer
from xpresso.testclient import TestClient


class OAuth2(OAuth2AuthorizationCodeBearer):
    authorization_url = "authorize"
    token_url = "token"


async def read_items(auth: OAuth2):
    return {"token": auth.token}


app = App([Path("/items/", get=read_items)])


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def test_no_token(client: TestClient):
    response = client.get("/items")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token(client: TestClient):
    response = client.get("/items", headers={"Authorization": "Non-existent testtoken"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_token(client: TestClient):
    response = client.get("/items", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"token": "testtoken"}
