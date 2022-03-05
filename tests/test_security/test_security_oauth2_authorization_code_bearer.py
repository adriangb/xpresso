from xpresso import App, Path
from xpresso.security import OAuth2AuthorizationCodeBearer, OAuth2Token, Security
from xpresso.testclient import TestClient
from xpresso.typing import Annotated

oauth2 = OAuth2AuthorizationCodeBearer(
    scheme_name="oauth2",
    authorization_url="authorize",
    token_url="token",
    scopes={"read": "read things", "write": "write things"},
)


oauth2_read = oauth2.require_scopes("read")


async def read_items(auth: Annotated[OAuth2Token, Security(oauth2_read)]):
    assert auth.required_scopes == {"read"}  # or do something to validate scopes
    return {"token": auth.token}


app = App([Path("/items/", get=read_items)])


client = TestClient(app)


def test_no_token():
    response = client.get("/items")
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_incorrect_token():
    response = client.get("/items", headers={"Authorization": "Non-existent testtoken"})
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Not authenticated"}


def test_token():
    response = client.get("/items", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"token": "testtoken"}


def test_dependency_override():
    with app.dependency_overrides as overrides:
        overrides[oauth2_read] = lambda: OAuth2Token(
            token="secret", required_scopes=frozenset(("read",))
        )

        client = TestClient(app)

        response = client.get("/items")
        assert response.status_code == 200, response.text
        assert response.json() == {"token": "secret"}
