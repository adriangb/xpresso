import inspect
import typing
from dataclasses import dataclass

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._extractors.api import ParameterExtractor
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


@dataclass(frozen=True)
class ParameterExtractorBase(ParameterExtractor):
    field: ModelField
    loc: typing.Tuple[str, ...]
    name: str
    in_: typing.ClassVar[str]

    def validate(self, values: typing.Optional[Some[typing.Any]]) -> typing.Any:
        """Validate after parsing. Only used by the top-level body"""
        if values is None:
            if self.field.required is False:
                return self.field.get_default()
            else:
                raise RequestValidationError(
                    [
                        ErrorWrapper(
                            ValueError(f"Missing required {self.in_} parameter"),
                            loc=self.loc,
                        )
                    ]
                )
        val, errs = self.field.validate(values.value, {}, loc=self.loc)
        if errs:
            if isinstance(errs, ErrorWrapper):
                errs = [errs]
            errs = typing.cast(typing.List[ErrorWrapper], errs)
            raise RequestValidationError(errs)
        return val


def get_basic_param_info(
    param: inspect.Parameter, alias: typing.Optional[str], in_: str
) -> typing.Tuple[ModelField, str, typing.Tuple[str, ...]]:
    field = model_field_from_param(param)
    name = alias or field.alias
    loc = (in_, name)
    return (field, name, loc)
