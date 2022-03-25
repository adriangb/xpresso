import typing
from typing import List, Type

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic import create_model
from pydantic.error_wrappers import ErrorWrapper
from starlette.exceptions import HTTPException as HTTPException  # noqa: F401
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

_RequestErrorModel: Type[BaseModel] = create_model("Request")  # type: ignore
_WebSocketErrorModel: Type[BaseModel] = create_model("WebSocket")  # type: ignore


class RequestValidationError(PydanticValidationError):
    raw_errors: List[ErrorWrapper]

    def __init__(
        self,
        errors: typing.Sequence[ErrorWrapper],
        status_code: int = HTTP_422_UNPROCESSABLE_ENTITY,
    ) -> None:
        super().__init__(errors, _RequestErrorModel)
        self.status_code = status_code


class WebSocketValidationError(PydanticValidationError):
    def __init__(
        self,
        errors: typing.Sequence[ErrorWrapper],
    ) -> None:
        super().__init__(errors, _WebSocketErrorModel)
