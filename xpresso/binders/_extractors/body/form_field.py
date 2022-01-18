import inspect
import typing
from dataclasses import dataclass

from pydantic.error_wrappers import ErrorWrapper
from starlette.datastructures import FormData

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._extractors.api import BodyExtractor, BodyExtractorMarker
from xpresso.binders._extractors.exceptions import InvalidSerialization
from xpresso.binders._extractors.form_utils import (
    Extractor,
    UnexpectedFileReceived,
    get_extractor,
)
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


@dataclass(frozen=True)
class FormFieldBodyExtractor(BodyExtractor, BodyExtractorMarker):
    alias: typing.Optional[str]
    style: str
    explode: bool
    name: str
    extractor: Extractor

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        try:
            return self.extractor(name=self.name, params=form.multi_items())
        except InvalidSerialization:
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=TypeError("Data is not a valid URL encoded form"),
                        loc=tuple((*loc, self.name)),
                    )
                ]
            )
        except UnexpectedFileReceived as exc:
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=exc,
                        loc=tuple((*loc, self.name)),
                    )
                ]
            )

    # These are implemented to work around pecularities of hashing bound methods on Python 3.7
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, __o: object) -> bool:
        return self is __o


@dataclass(frozen=True)
class FormFieldBodyExtractorMarker(BodyExtractorMarker):
    alias: typing.Optional[str]
    style: str
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        name = self.alias or param.name
        extractor = get_extractor(
            style=self.style, explode=self.explode, field=model_field_from_param(param)
        )
        return FormFieldBodyExtractor(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            name=name,
            extractor=extractor,
        )
