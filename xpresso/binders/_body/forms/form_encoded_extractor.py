import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from starlette.datastructures import FormData

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import SupportsXpressoFormDataFieldExtractor
from xpresso.binders._utils.forms import Extractor as FormExtractor
from xpresso.binders._utils.forms import UnexpectedFileReceived, get_extractor
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


class _FormEncodedFieldExtractor(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool
    field_name: str
    extractor: FormExtractor

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some]:
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

    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldExtractor:
        field_name = self.alias or param.name
        extractor = get_extractor(
            style=self.style, explode=self.explode, field=model_field_from_param(param)
        )
        return _FormEncodedFieldExtractor(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            field_name=field_name,
            extractor=extractor,
        )
