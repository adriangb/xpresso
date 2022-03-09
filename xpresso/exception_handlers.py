from typing import Awaitable, Callable, Type, TypeVar, Union

from fastapi import Response
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from xpresso.encoders.json import JsonableEncoder
from xpresso.exceptions import RequestValidationError

ExcType = TypeVar("ExcType", bound=Exception, contravariant=True)


class ExcHandler:
    def __init__(
        self,
        exc: Union[Type[ExcType], int],
        handler: Callable[[Request, ExcType], Union[Awaitable[Response], Response]],
    ) -> None:
        self.exc = exc
        self.handler = handler


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"detail": exc.detail}, status_code=exc.status_code, headers=headers
        )
    else:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


_ENCODER = JsonableEncoder()


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        _ENCODER({"detail": exc.errors()}),
        status_code=exc.status_code,
    )
