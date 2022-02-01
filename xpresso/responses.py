from typing import Any, Iterable, Mapping, Optional, Union

from pydantic import BaseModel, Field
from starlette.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)

from xpresso._utils.asgi_scope_extension import XpressoASGIExtension
from xpresso.exceptions import XpressoError
from xpresso.openapi.models import Example, ResponseHeader
from xpresso.requests import Request

__all__ = (
    "get_response",
    "set_response",
    "ResponseSpec",
    "JsonResponseSpec",
    "FileResponseSpec",
    "HTMLResponseSpec",
    "PlainTextResponseSpec",
    "Response",
    "JSONResponse",
    "StreamingResponse",
    "HTMLResponse",
    "PlainTextResponse",
)


def get_response(request: Request) -> Response:
    try:
        return request.scope["extensions"]["xpresso"]["response"]  # type: ignore[return-type]
    except KeyError:
        raise LookupError(
            "xpresso.responses.get_response was called"
            " before the endpoint has finished executing or the endpoint raised an exception"
        )


def set_response(request: Request, response: Response) -> None:
    xpresso_scope: XpressoASGIExtension = request.scope["extensions"]["xpresso"]
    if xpresso_scope["response_sent"]:
        raise XpressoError(
            'set_response() can only be used from "endpoint" scoped dependendencies'
        )
    xpresso_scope["response"] = response  # type: ignore[assignment]


class ResponseSpec(BaseModel):
    description: str
    model: Any = None
    media_type: Optional[str] = None
    headers: Optional[Mapping[str, Union[ResponseHeader, str]]] = None
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


class JsonResponseSpec(ResponseSpec):
    model: Any = Field(default={})
    media_type: str = "application/json"


class FileResponseSpec(ResponseSpec):
    model: Any = Field(default=bytes)
    media_type: str = "application/octetstream"


class HTMLResponseSpec(ResponseSpec):
    model: Any = Field(default=str)
    media_type: str = "text/html"


class PlainTextResponseSpec(ResponseSpec):
    model: str
    media_type = "text/plain"


Responses = Mapping[Union[int, str], Union[Iterable[ResponseSpec], ResponseSpec]]
