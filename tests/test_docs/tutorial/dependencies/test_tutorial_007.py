import json
from typing import Any, Dict, Iterable

import pytest

from docs_src.tutorial.dependencies.tutorial_007 import app
from xpresso.testclient import TestClient


@pytest.mark.parametrize(
    "roles,status_code,json_response",
    [
        (
            [],
            403,
            json.load(
                open("docs_src/tutorial/dependencies/tutorial_007_response_001.json")
            ),
        ),
        (
            ["user"],
            403,
            json.load(
                open("docs_src/tutorial/dependencies/tutorial_007_response_002.json")
            ),
        ),
        (
            ["user", "items-user"],
            200,
            json.load(
                open("docs_src/tutorial/dependencies/tutorial_007_response_003.json")
            ),
        ),
    ],
)
def test_get_item_authorization(
    roles: Iterable[str],
    status_code: int,
    json_response: Dict[str, Any],
):
    client = TestClient(app)
    params = [("roles", role) for role in roles]
    response = client.get("/items/foobar", params=params)
    assert response.status_code == status_code, response.content
    assert response.json() == json_response


@pytest.mark.parametrize(
    "roles,status_code,json_response",
    [
        (
            [],
            403,
            json.load(
                open("docs_src/tutorial/dependencies/tutorial_007_response_001.json")
            ),
        ),
        (
            ["user"],
            403,
            json.load(
                open("docs_src/tutorial/dependencies/tutorial_007_response_002.json")
            ),
        ),
        (["user", "items-user"], 403, {"detail": "Missing roles: ['items-admin']"}),
        (["user", "items-user", "items-admin"], 200, None),
    ],
)
def test_delete_item_authorization(
    roles: Iterable[str],
    status_code: int,
    json_response: Dict[str, Any],
):
    client = TestClient(app)
    params = [("roles", role) for role in roles]
    response = client.delete("/items/foobar", params=params)
    assert response.status_code == status_code, response.content
    assert response.json() == json_response
