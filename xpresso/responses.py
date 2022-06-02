from typing import Any, Mapping, NamedTuple, Optional, Union

from pydantic import BaseModel
from starlette.responses import FileResponse as FileResponse  # noqa: F401
from starlette.responses import HTMLResponse as HTMLResponse  # noqa: F401
from starlette.responses import JSONResponse as JSONResponse  # noqa: F401
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa: F401
from starlette.responses import RedirectResponse as RedirectResponse  # noqa: F401
from starlette.responses import Response as Response  # noqa: F401
from starlette.responses import StreamingResponse as StreamingResponse  # noqa: F401

from xpresso._utils.asgi import XpressoHTTPExtension
from xpresso._utils.typing import Literal
from xpresso.openapi.models import Example, ResponseHeader
from xpresso.requests import Request


def get_response(request: Request) -> Response:
    xpresso_extension: "XpressoHTTPExtension" = request.scope["extensions"]["xpresso"]  # type: ignore  # for Pylance
    if xpresso_extension.response is None:
        raise LookupError(
            "xpresso.responses.get_response was called"
            " before the endpoint has finished executing or the endpoint raised an exception"
        )
    return xpresso_extension.response


def set_response(request: Request, response: Response) -> None:
    xpresso_extension: "XpressoHTTPExtension" = request.scope["extensions"]["xpresso"]  # type: ignore  # for Pylance
    if xpresso_extension.response_sent:
        raise RuntimeError(
            'set_response() can only be used from "endpoint" scoped dependendencies'
        )
    xpresso_extension.response = response


class TypeUnset:
    ...


class ResponseModel(NamedTuple):
    model: Any = TypeUnset
    examples: Optional[Mapping[str, Union[Example, Any]]] = None


class ResponseSpec(BaseModel):
    description: Optional[str] = None
    content: Optional[Mapping[str, Union[ResponseModel, type]]] = None
    headers: Optional[Mapping[str, Union[ResponseHeader, str]]] = None

    class Config:
        arbitrary_types_allowed = True


class FileResponseSpec(ResponseSpec):
    content: Optional[Mapping[str, Union[ResponseModel, type]]] = {
        "application/octetstream": ResponseModel(bytes)
    }


class HTMLResponseSpec(ResponseSpec):
    content: Optional[Mapping[str, Union[ResponseModel, type]]] = {
        "text/html": ResponseModel(str)
    }


class PlainTextResponseSpec(ResponseSpec):
    content: Optional[Mapping[str, Union[ResponseModel, type]]] = {
        "text/plain": ResponseModel(str)
    }


ResponseStatusCode = Union[Literal["default", "2XX", "3XX", "4XX", "5XX"], int]
