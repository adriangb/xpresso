from typing import Any, Dict, Generator, Optional

import pytest
from pydantic import BaseModel

from xpresso import App, Dependant, FromFormData, Path, Security
from xpresso.security import OAuth2, OAuth2PasswordRequestFormStrict
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

reusable_oauth2 = OAuth2(
    flows={
        "password": {
            "tokenUrl": "token",
            "scopes": {"read:users": "Read the users", "write:users": "Create users"},
        }
    },
    auto_error=False,
)


class User(BaseModel):
    username: str


def get_current_user(oauth_header: Annotated[Optional[str], Security(reusable_oauth2)]):
    if oauth_header is None:
        return None
    user = User(username=oauth_header)
    return user


def login(form_data: FromFormData[OAuth2PasswordRequestFormStrict]):
    return form_data


def read_users_me(current_user: Annotated[Optional[User], Dependant(get_current_user)]):
    if current_user is None:
        return {"msg": "Create an account first"}
    return current_user


app = App(
    [
        Path("/users/me", get=read_users_me),
        Path("/login", post=login),
    ]
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


openapi_schema: Dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {"title": "API", "version": "0.1.0"},
    "paths": {
        "/login": {
            "post": {
                "responses": {
                    "200": {"description": "Successful Response"},
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
                "requestBody": {
                    "content": {
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "required": [
                                    "grant_type",
                                    "username",
                                    "password",
                                    "scopes",
                                ],
                                "type": "object",
                                "properties": {
                                    "grant_type": {
                                        "title": "Grant Type",
                                        "enum": ["password"],
                                        "type": "string",
                                    },
                                    "username": {"title": "Username", "type": "string"},
                                    "password": {"title": "Password", "type": "string"},
                                    "scopes": {
                                        "title": "Scopes",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "client_id": {
                                        "title": "Client Id",
                                        "type": "string",
                                    },
                                    "client_secret": {
                                        "title": "Client Secret",
                                        "type": "string",
                                    },
                                },
                            },
                            "encoding": {
                                "grant_type": {"style": "form", "explode": True},
                                "username": {"style": "form", "explode": True},
                                "password": {"style": "form", "explode": True},
                                "scopes": {"style": "spaceDelimited", "explode": False},
                                "client_id": {"style": "form", "explode": True},
                                "client_secret": {"style": "form", "explode": True},
                            },
                        }
                    },
                    "required": True,
                },
            }
        },
        "/users/me": {
            "get": {
                "responses": {"200": {"description": "Successful Response"}},
                "security": [{"OAuth2": []}],
            }
        },
    },
    "components": {
        "schemas": {
            "ValidationError": {
                "title": "ValidationError",
                "required": ["loc", "msg", "type"],
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                    },
                    "msg": {"title": "Message", "type": "string"},
                    "type": {"title": "Error Type", "type": "string"},
                },
            },
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Detail",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
            },
        },
        "securitySchemes": {
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "scopes": {
                            "read:users": "Read the users",
                            "write:users": "Create users",
                        },
                        "tokenUrl": "token",
                    }
                },
            }
        },
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
    assert response.status_code == 200, response.text
    assert response.json() == {"msg": "Create an account first"}


required_params = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", "username"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", "password"],
            "msg": "field required",
            "type": "value_error.missing",
        },
    ]
}

grant_type_required = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
}

grant_type_incorrect = {
    "detail": [
        {
            "loc": ["body", "grant_type"],
            "msg": "unexpected value; permitted: 'password'",
            "type": "value_error.const",
            "ctx": {"given": "incorrect", "permitted": ["password"]},
        }
    ]
}


@pytest.mark.parametrize(
    "data,expected_status,expected_response",
    [
        (None, 422, required_params),
        ({"username": "johndoe", "password": "secret"}, 422, grant_type_required),
        (
            {"username": "johndoe", "password": "secret", "grant_type": "incorrect"},
            422,
            grant_type_incorrect,
        ),
        (
            {"username": "johndoe", "password": "secret", "grant_type": "password"},
            200,
            {
                "grant_type": "password",
                "username": "johndoe",
                "password": "secret",
                "scopes": [],
                "client_id": None,
                "client_secret": None,
            },
        ),
    ],
)
def test_strict_login(data, expected_status, expected_response, client: TestClient):
    response = client.post(
        "/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == expected_status
    assert response.json() == expected_response
