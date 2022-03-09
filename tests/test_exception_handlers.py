import pytest
from starlette.responses import JSONResponse

from xpresso import App, FromPath, HTTPException, Path, Request
from xpresso.exception_handlers import ExcHandler
from xpresso.exceptions import RequestValidationError
from xpresso.testclient import TestClient


def http_exception_handler(request: Request, exception: HTTPException):
    return JSONResponse({"exception": "http-exception"})


def request_validation_exception_handler(
    request: Request, exception: RequestValidationError
):
    return JSONResponse({"exception": "request-validation"})


def server_error_exception_handler(request: Request, exception: Exception):
    return JSONResponse(status_code=500, content={"exception": "server-error"})


def route_with_http_exception():
    raise HTTPException(status_code=400)


def route_with_request_validation_exception(param: FromPath[int]):
    pass  # pragma: no cover


def route_with_server_error():
    raise RuntimeError("Oops!")


app = App(
    routes=[
        Path("/http-exception", get=route_with_http_exception),
        Path(
            "/request-validation/{param}/", get=route_with_request_validation_exception
        ),
        Path("/server-error", get=route_with_server_error),
    ],
    exception_handlers=[
        ExcHandler(HTTPException, http_exception_handler),
        ExcHandler(RequestValidationError, request_validation_exception_handler),
        ExcHandler(Exception, server_error_exception_handler),
    ],
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
    with pytest.raises(RuntimeError):
        client.get("/server-error")


def test_override_server_error_exception_response():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/server-error")
    assert response.status_code == 500
    assert response.json() == {"exception": "server-error"}
