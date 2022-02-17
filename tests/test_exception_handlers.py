import pytest

from xpresso import App, FromPath, HTTPException, Path, Request
from xpresso.exceptions import RequestValidationError
from xpresso.responses import JSONResponse
from xpresso.testclient import TestClient


def test_override_base_error_handler() -> None:
    async def custom_server_error_from_exception(request: Request, exc: Exception):
        return JSONResponse(
            {"detail": "Custom Server Error from Exception"}, status_code=500
        )

    async def raise_exception() -> None:
        raise Exception

    async def custom_server_error_from_500(request: Request, exc: Exception):
        return JSONResponse(
            {"detail": "Custom Server Error from HTTPException(500)"}, status_code=500
        )

    async def raise_500() -> None:
        raise HTTPException(500)

    app = App(
        routes=[
            Path("/raise-exception", get=raise_exception),
            Path("/raise-500", get=raise_500),
        ],
        exception_handlers={
            Exception: custom_server_error_from_exception,
            500: custom_server_error_from_500,
        },
    )

    client = TestClient(app)

    resp = client.get("/raise-exception")
    assert resp.status_code == 500, resp.content
    assert resp.json() == {"detail": "Custom Server Error from Exception"}

    resp = client.get("/raise-500")
    assert resp.status_code == 500, resp.content
    assert resp.json() == {"detail": "Custom Server Error from HTTPException(500)"}


def http_exception_handler(request: Request, exception: Exception):
    return JSONResponse({"exception": "http-exception"})


def request_validation_exception_handler(request: Request, exception: Exception):
    return JSONResponse({"exception": "request-validation"})


def server_error_exception_handler(request: Request, exception: Exception):
    raise exception


def route_with_http_exception():
    raise HTTPException(status_code=400)


def route_with_request_validation_exception(param: FromPath[int]):
    pass  # pragma: no cover


class UnhanldedException(Exception):
    pass


def route_with_server_error():
    raise UnhanldedException


app = App(
    routes=[
        Path("/server-error", get=route_with_server_error),
        Path(
            "/request-validation/{param}/", get=route_with_request_validation_exception
        ),
        Path("/http-exception", get=route_with_http_exception),
    ],
    exception_handlers={
        HTTPException: http_exception_handler,
        RequestValidationError: request_validation_exception_handler,
        Exception: server_error_exception_handler,
    },
)

client = TestClient(app)


def test_override_http_exception():
    response = client.get("/http-exception")
    assert response.status_code == 200
    assert response.json() == {"exception": "http-exception"}


def test_override_request_validation_exception():
    response = client.get("/request-validation/invalid")
    assert response.status_code == 200
    assert response.json() == {"exception": "request-validation"}


def test_override_server_error_exception_raises():
    with pytest.raises(UnhanldedException):
        client.get("/server-error")


def test_override_server_error_exception_response():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/server-error")
    assert response.status_code == 500
    assert response.json() == {"exception": "server-error"}
