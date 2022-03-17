import pytest
import starlette.routing

from xpresso import App, FromFile, FromJson, Operation, Path
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


def test_multiple_bodies_are_not_allowed() -> None:
    async def endpoint(
        body1: FromFile[bytes],
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
