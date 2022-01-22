"""Tests for JSON body deserialization
"""
import sys
import typing

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from xpresso import App, Dependant, Path
from xpresso.exceptions import XpressoError
from xpresso.responses import get_response, set_response


@pytest.mark.parametrize("scope", ["operation", "connection"])
def test_get_response(scope: typing.Any) -> None:
    """ResponseProxy can be used to get the final Response from within a dependency"""

    def dependency(request: Request) -> typing.Generator[None, None, None]:
        try:
            get_response(request)
        except LookupError:
            pass
        else:
            raise AssertionError("Should have raised LookupError")  # pragma: no cover
        yield
        response = get_response(request)
        assert response.status_code == 404
        response.status_code = 405

    async def endpoint(
        dep: Annotated[None, Dependant(dependency, scope=scope)]
    ) -> Response:
        return Response(status_code=404)

    app = App([Path("/", get=endpoint)])

    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == (405 if scope == "operation" else 404)


def test_get_response_connection_scope() -> None:
    """Connection scoped dependencies can get a copy of the Response but can't modify it"""

    def dependency(request: Request) -> typing.Generator[None, None, None]:
        yield
        response = get_response(request)
        assert response.status_code == 405
        # this should have no effect since the Response is already sent
        response.status_code = 404

    async def endpoint(
        dep: Annotated[None, Dependant(dependency, scope="connection")]
    ) -> Response:
        return Response(status_code=405)

    app = App([Path("/", get=endpoint)])

    with TestClient(app) as client:
        resp = client.get("/")
    assert (
        resp.status_code == 405
    )  # does not pick up on 404 because response was alredy sent


def test_set_response() -> None:
    def dependency(request: Request) -> typing.Generator[None, None, None]:
        yield
        set_response(request, JSONResponse({"foo": "bar"}))

    async def endpoint() -> Response:
        return Response()

    app = App(
        [
            Path(
                "/",
                get=endpoint,
                dependencies=[Dependant(dependency, scope="operation")],
            )
        ]
    )

    with TestClient(app) as client:
        resp = client.get("/")

    assert resp.status_code == 200, resp.content


def test_set_response_operation_scope() -> None:
    def dependency(request: Request) -> typing.Generator[None, None, None]:
        yield
        set_response(request, JSONResponse({"foo": "bar"}))

    async def endpoint() -> Response:
        return Response()

    app = App(
        [
            Path(
                "/",
                get=endpoint,
                dependencies=[Dependant(dependency, scope="connection")],
            )
        ]
    )

    client = TestClient(app)
    with pytest.raises(
        XpressoError, match='can only be used from "operation" scoped dependendencies'
    ):
        client.get("/")
