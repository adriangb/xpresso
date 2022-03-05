# from xpresso import App, Depends, Path
# from xpresso.security import OAuth2AuthorizationCodeBearer, OAuth2Token, RequireScopes
# from xpresso.testclient import TestClient
# from xpresso.typing import Annotated


# class OAuth2(OAuth2AuthorizationCodeBearer):
#     scheme_name = "oauth2"
#     authorization_url = "authorize"
#     token_url = "token"


# oauth2 = OAuth2AuthorizationCodeBearer(
#     scheme_name="oauth2",
#     authorization_url="authorize",
#     token_url="token",
#     scopes={"read": "read things", "write": "write things"},
# )


# Auth2Read = Annotated[OAuth2Token, Depends(RequireScopes(oauth2, ["read"]))]


# async def read_items(auth: Auth2Read):
#     assert auth.required_scopes == {"read"}  # or do something to validate scopes
#     return {"token": auth.token}


# app = App([Path("/items/", get=read_items)])


# client = TestClient(app)


# def test_no_token():
#     response = client.get("/items")
#     assert response.status_code == 401, response.text
#     assert response.json() == {"detail": "Not authenticated"}


# def test_incorrect_token():
#     response = client.get("/items", headers={"Authorization": "Non-existent testtoken"})
#     assert response.status_code == 401, response.text
#     assert response.json() == {"detail": "Not authenticated"}


# def test_token():
#     response = client.get("/items", headers={"Authorization": "Bearer testtoken"})
#     assert response.status_code == 200, response.text
#     assert response.json() == {"token": "testtoken"}
