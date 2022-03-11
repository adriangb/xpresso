import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField

from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


def validate_body_field(
    values: typing.Optional[Some],
    *,
    field: ModelField,
    loc: typing.Tuple[typing.Union[str, int], ...]
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
