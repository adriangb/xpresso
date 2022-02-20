import inspect
import typing

from starlette.datastructures import FormData

import xpresso.openapi.models as openapi_models
from xpresso._utils.compat import Protocol
from xpresso._utils.typing import Some
from xpresso.binders.api import ModelNameMap, Schemas


class FormFieldOpenAPIProvider(Protocol):
    @property
    def field_name(self) -> str:
        ...

    @property
    def include_in_schema(self) -> bool:
        ...

    def get_models(self) -> typing.List[type]:
        raise NotImplementedError

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        raise NotImplementedError

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        raise NotImplementedError


class FormDataFieldOpenapiMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> FormFieldOpenAPIProvider:
        raise NotImplementedError


class FormDataExtractor(Protocol):
    @property
    def field_name(self) -> str:
        ...

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        raise NotImplementedError


class FormDataExtractorMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> FormDataExtractor:
        raise NotImplementedError


class FormFieldMarker(typing.NamedTuple):
    openapi_marker: FormDataFieldOpenapiMarker
    extractor_marker: FormDataExtractorMarker
