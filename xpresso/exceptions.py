import typing
from typing import List, Type

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from pydantic import create_model
from pydantic.error_wrappers import ErrorWrapper
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


class xpressoError(Exception):
    ...


# This should be upstreamed
class HTTPException(StarletteHTTPException, xpressoError):
    def __init__(
        self,
        status_code: int,
        detail: typing.Any = None,
        headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.headers = headers


_RequestErrorModel: Type[BaseModel] = create_model("Request")  # type: ignore


class RequestValidationError(PydanticValidationError, xpressoError):
    raw_errors: List[ErrorWrapper]

    def __init__(
        self,
        errors: typing.Optional[typing.List[ErrorWrapper]] = None,
        status_code: int = HTTP_422_UNPROCESSABLE_ENTITY,
    ) -> None:
        super().__init__(errors or [], _RequestErrorModel)
        self.status_code = status_code
