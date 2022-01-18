from typing import Any, Dict, Generator, Optional

import pytest

from xpresso import App, Path, Security
from xpresso.security import OAuth2PasswordBearer
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    description="OAuth2PasswordBearer security scheme",
    auto_error=False,
)


async def read_items(token: Annotated[Optional[str], Security(oauth2_scheme)]):
    if token is None:
        return {"msg": "Create an account first"}
    return {"token": token}


app = App([Path("/items/", get=read_items)])


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/items/": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Successful Response",
                    }
                },
                "security": [{"OAuth2PasswordBearer": []}],
            }
        }
    },
    "components": {
        "securitySchemes": {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {"password": {"scopes": {}, "tokenUrl": "/token"}},
                "description": "OAuth2PasswordBearer security scheme",
            }
        }
    },
}


def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == openapi_schema


def test_no_token(client: TestClient):
    response = client.get("/items")
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}


def test_token(client: TestClient):
    response = client.get("/items", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"token": "testtoken"}


def test_incorrect_token(client: TestClient):
    response = client.get("/items", headers={"Authorization": "Notexistent testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}
