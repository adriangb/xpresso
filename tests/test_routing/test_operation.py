from typing import Any, Dict

import pytest
import starlette.routing

from xpresso import App, FromJson, FromRawBody, Operation, Path
from xpresso.routing.operation import NotPreparedError
from xpresso.testclient import TestClient


async def endpoint_1() -> None:
    ...


async def endpoint_2() -> None:
    ...


def test_url_path_for_with_path_parameters() -> None:
    operation = Operation(endpoint_1, name="endpoint")
    with pytest.raises(starlette.routing.NoMatchFound):
        operation.url_path_for("endpoint", param="foobar")


def test_url_path_for_no_match() -> None:
    operation = Operation(endpoint_1, name="endpoint")
    with pytest.raises(starlette.routing.NoMatchFound):
        operation.url_path_for("not-operation")


def test_url_path_for_matches() -> None:
    operation = Operation(endpoint_1, name="endpoint")

    url = operation.url_path_for("endpoint")

    assert str(url) == "/"


def test_operation_comparison() -> None:
    assert Operation(endpoint_1) == Operation(endpoint_1)
    assert Operation(endpoint_1) != Operation(endpoint_2)


@pytest.mark.skip
def test_multiple_bodies_are_not_allowed() -> None:
    async def endpoint(
        body1: FromRawBody[bytes],
        body2: FromJson[str],
    ) -> None:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App(
        routes=[
            Path(
                "/test",
                post=endpoint,
            )
        ]
    )

    client = TestClient(app)
    with pytest.raises(
        ValueError, match=r"Only 1 top level body is allowed in OpenAPI specs"
    ):
        client.get("/openapi.json")


def test_usage_outside_of_xpresso() -> None:
    app = starlette.routing.Router(routes=[Path("/", get=endpoint_1)])

    msg = r"Operation.prepare\(\) was never called on this Operation"

    # error triggered with lifespan
    with TestClient(app) as client:
        with pytest.raises(NotPreparedError, match=msg):
            client.get("/")

    # error triggered without lifespan
    client = TestClient(app)
    with pytest.raises(NotPreparedError, match=msg):
        client.get("/")


def test_include_in_schema() -> None:
    async def endpoint() -> None:
        ...

    app = App([Path("/", get=Operation(endpoint, include_in_schema=False))])

    client = TestClient(app)

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {"/": {}},
    }

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
