import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso.exceptions import RequestValidationError, WebSocketValidationError
from xpresso.typing import Some


async def validate_param_field(
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


def validate_body_field(
    values: typing.Optional[Some],
    *,
    field: ModelField,
    loc: typing.Tuple[typing.Union[str, int], ...],
) -> typing.Any:
    """Validate after extraction. Should only be used by the top-level body"""
    if values is None:
        if field.required is False:
            return field.get_default()
        else:
            raise RequestValidationError(
                [ErrorWrapper(ValueError("Missing required value"), loc=loc)]
            )
    val, err_or_errors = field.validate(values.value, {}, loc=loc)
    if err_or_errors:
        errors: typing.List[ErrorWrapper]
        if isinstance(err_or_errors, ErrorWrapper):
            errors = [err_or_errors]
        else:
            errors = typing.cast(
                typing.List[ErrorWrapper], err_or_errors
            )  # already a list
        raise RequestValidationError(errors)
    return val
