import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from starlette.datastructures import FormData

from xpresso._utils.typing import Some, model_field_from_param
from xpresso.binders._body.form_field import FormDataExtractor
from xpresso.binders._utils.forms import (
    Extractor,
    UnexpectedFileReceived,
    get_extractor,
)
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError


class FormEncodedFieldExtractor:
    __slots__ = ("alias", "style", "explode", "field_name", "extractor")

    def __init__(
        self,
        alias: typing.Optional[str],
        style: str,
        explode: bool,
        field_name: str,
        extractor: Extractor,
    ) -> None:
        self.alias = alias
        self.style = style
        self.explode = explode
        self.field_name = field_name
        self.extractor = extractor

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        try:
            return self.extractor(name=self.field_name, params=form.multi_items())
        except InvalidSerialization as e:
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=TypeError("Data is not a valid URL encoded form"),
                        loc=tuple((*loc, self.field_name)),
                    )
                ]
            ) from e
        except UnexpectedFileReceived as exc:
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=exc,
                        loc=tuple((*loc, self.field_name)),
                    )
                ]
            ) from exc


class FormEncodedFieldExtractorMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> FormDataExtractor:
        field_name = self.alias or param.name
        extractor = get_extractor(
            style=self.style, explode=self.explode, field=model_field_from_param(param)
        )
        return FormEncodedFieldExtractor(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            field_name=field_name,
            extractor=extractor,
        )
