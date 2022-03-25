from typing import Awaitable, Callable, Type, TypeVar, Union

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from xpresso.encoders import JsonableEncoder
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


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None) or {},
    )


_ENCODER = JsonableEncoder()


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        _ENCODER({"detail": exc.errors()}),
        status_code=exc.status_code,
    )
