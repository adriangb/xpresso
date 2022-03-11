from typing import Any, Dict, Iterable, List, Optional, Union

from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection

import xpresso.openapi.models as openapi_models
from xpresso._utils.compat import Protocol


class SupportsExtractor(Protocol):
    def extract(self, connection: HTTPConnection) -> Any:
        raise NotImplementedError


class SupportsBodyExtractor(SupportsExtractor, Protocol):
    def matches_media_type(self, media_type: Optional[str]) -> bool:
        """Check if this extractor can extract the given media type"""
        raise NotImplementedError


class SupportsFieldExtractor(Protocol):
    # APIs to support being a field in a FormData or Multipart request
    async def extract_from_field(
        self,
        field: Union[str, UploadFile],
        *,
        loc: Iterable[Union[str, int]],
    ) -> Any:
        """Extract from a form field"""
        raise NotImplementedError


Model = type
ModelNameMap = Dict[Model, str]
Schemas = Dict[str, Union[openapi_models.Schema, openapi_models.Reference]]


class _SupportsGetModels(Protocol):
    def get_models(self) -> List[type]:
        """Collect all of the types that OpenAPI schemas will be
        produced from.

        Xpresso will then assign a schema name to each type and pass
        that back via the ModelNameMap parameter.

        This ensures that all schema models have a unique name,
        even if their Python class names conflict.
        """
        raise NotImplementedError


class SupportsOpenAPIParameter(_SupportsGetModels, Protocol):
    @property
    def include_in_schema(self) -> bool:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def in_(self) -> openapi_models.ParameterLocations:
        ...

    def get_openapi_parameter(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.ConcreteParameter:
        """Generate the OpenAPI spec for this parameter"""
        raise NotImplementedError


class SupportsOpenAPIBody(_SupportsGetModels, Protocol):
    @property
    def include_in_schema(self) -> bool:
        ...

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        """Generate the OpenAPI spec for this request body"""
        raise NotImplementedError


class SupportsOpenAPIField(_SupportsGetModels, Protocol):
    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        """Get the Encoding for this field.

        If this is a URL-encoded form field (as part of
        an application/x-www-form-urlencoded) the Encoding
        MAY include the `style` and `explode` sections.

        For all other field types, it can only include the
        `contentType` and `Headers` section.
        """
        raise NotImplementedError

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        """Get the Schema for this field.

        This will be used to assemble the Form's schema,
        which is an object schema having as properties the schemas
        for each field.
        """
        raise NotImplementedError
