import inspect
import typing

from starlette.datastructures import FormData

import xpresso.openapi.models as openapi_models
from xpresso._utils.compat import Protocol
from xpresso.binders.api import ModelNameMap, Schemas
from xpresso.typing import Some


class SupportsXpressoFormDataFieldOpenAPI(Protocol):
    @property
    def field_name(self) -> str:
        ...

    @property
    def include_in_schema(self) -> bool:
        ...

    def get_models(self) -> typing.Iterable[type]:
        ...

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        ...

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        ...


class SupportsXpressoFormDataFieldOpenAPIMarker(Protocol):
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldOpenAPI:
        ...


class SupportsXpressoFormDataFieldExtractor(Protocol):
    @property
    def field_name(self) -> str:
        ...

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some]:
        ...


class SupportsXpressoFormDataFieldExtractorMarker(Protocol):
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldExtractor:
        ...


class FormFieldMarker(typing.NamedTuple):
    openapi_marker: SupportsXpressoFormDataFieldOpenAPIMarker
    extractor_marker: SupportsXpressoFormDataFieldExtractorMarker
