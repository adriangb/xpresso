from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from xpresso.encoders.json import JsonableEncoder
from xpresso.exceptions import RequestValidationError

encoder = JsonableEncoder()


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"detail": exc.detail}, status_code=exc.status_code, headers=headers
        )
    else:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        encoder({"detail": exc.errors()}),
        status_code=exc.status_code,
    )
