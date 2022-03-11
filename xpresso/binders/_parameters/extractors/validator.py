import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso.exceptions import RequestValidationError, WebSocketValidationError
from xpresso.typing import Some


async def validate(
    field: ModelField,
    name: str,
    in_: str,
    values: typing.Optional[Some],
    connection: HTTPConnection,
) -> typing.Any:
    """Validate after parsing. Only used by the top-level body"""
    if values is None:
        if field.required is False:
            return field.get_default()
        else:
            err = [
                ErrorWrapper(
                    ValueError(f"Missing required {in_} parameter"),
                    loc=(in_, name),
                )
            ]
            if connection.scope["type"] == "websocket":
                raise WebSocketValidationError(err)
            raise RequestValidationError(err)
    val, errs = field.validate(values.value, {}, loc=(in_, name))
    if errs:
        if isinstance(errs, ErrorWrapper):
            errs = [errs]
        errs = typing.cast(typing.List[ErrorWrapper], errs)
        if connection.scope["type"] == "websocket":
            raise WebSocketValidationError(errs)
        raise RequestValidationError(errs)
    return val
