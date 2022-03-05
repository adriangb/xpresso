# from typing import Optional, Union

# from pydantic import BaseModel

# from xpresso import App, Depends, Path
# from xpresso.security import (
#     APIKeyHeader,
#     OAuth2AuthorizationCodeBearer,
#     RequireScopes,
#     SecurityModel,
# )
# from xpresso.testclient import TestClient
# from xpresso.typing import Annotated


# class APIKey1(APIKeyHeader):
#     scheme_name = "apikey1"
#     name = "key1"


# apikey1 = APIKeyHeader(name="key1", scheme_name="apikey1")
# apikey2 = APIKeyHeader(name="key2", scheme_name="apikey2")
# oauth2 = OAuth2AuthorizationCodeBearer(
#     token_url="token",
#     authorization_url="authorize",
#     scheme_name="oauth",
#     scopes={"read": "read things", "write": "write things"},
#     unauthorized_error=None,
# )


# class APIKeys(SecurityModel):
#     key1: Annotated[str, Depends(apikey1)]
#     key2: Annotated[str, Depends(apikey2)]


# oauth2_read = RequireScopes(oauth2, ["read"])


# class User(BaseModel):
#     username: str


# def get_current_user(
#     auth: SecurityModelUnion[Union[Optional[APIKeys], Optional[oauth2_read]]]
# ):
#     if auth.apikeys is not None:
#         assert auth.apikeys.key2.api_key
#         return User(username=auth.apikeys.key1.api_key)
#     if auth.oauth is not None:
#         assert auth.oauth.required_scopes  # or something with the token
#         return User(username=auth.oauth.token)


# def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
#     return current_user


# app = App([Path("/users/me", get=read_current_user)])


# client = TestClient(app)


# def test_security_api_key_both_keys():
#     response = client.get("/users/me", headers={"key1": "secret", "key2": "foobarbaz"})
#     assert response.status_code == 200, response.text
#     assert response.json() == {"username": "secret"}


# def test_security_api_key_missing_one_key():
#     response = client.get("/users/me", headers={"key1": "secret"})
#     assert response.status_code == 401, response.text


# def test_security_api_key_no_key():
#     response = client.get("/users/me")
#     assert response.status_code == 401, response.text
#     assert response.json() == {"detail": "Not authenticated"}


# def test_no_auth():
#     response = client.get("/users/me")
#     assert response.status_code == 401, response.text
#     assert response.json() == {"detail": "Not authenticated"}


# def test_incorrect_token():
#     response = client.get(
#         "/users/me", headers={"Authorization": "Non-existent testtoken"}
#     )
#     assert response.status_code == 401, response.text
#     assert response.json() == {"detail": "Not authenticated"}


# def test_incorrect_token_with_api_keys():
#     response = client.get(
#         "/users/me",
#         headers={
#             "Authorization": "Bearer testtoken",
#             "key1": "secret",
#             "key2": "foobarbaz",
#         },
#     )
#     assert response.status_code == 200, response.text
#     assert response.json() == {"username": "secret"}


# def test_token():
#     response = client.get("/users/me", headers={"Authorization": "Bearer testtoken"})
#     assert response.status_code == 200, response.text
#     assert response.json() == {"username": "testtoken"}
