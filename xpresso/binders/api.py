import inspect
import sys
from typing import Any, Dict, Iterable, List, Optional, Union

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from starlette.datastructures import FormData, UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso.openapi import models
from xpresso.typing import Some

Model = type
ModelNameMap = Dict[Model, str]
Schemas = Dict[str, Union[models.Schema, models.Reference]]


class BodyExtractor(Protocol):
    async def extract_from_request(self, request: Request) -> Any:
        """Extract from top level request"""
        raise NotImplementedError

    async def extract_from_form(
        self,
        form: FormData,
        *,
        loc: Iterable[Union[str, int]],
    ) -> Optional[Some[Any]]:
        """Extract from a form"""
        raise NotImplementedError

    async def extract_from_field(
        self,
        field: Union[str, UploadFile],
        *,
        loc: Iterable[Union[str, int]],
    ) -> Any:
        """Extract from a form field"""
        raise NotImplementedError

    def matches_media_type(self, media_type: Optional[str]) -> bool:
        """Check if this extractor can extract the given media type"""
        raise NotImplementedError


class BodyExtractorMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        """Hook to pull information from the Python parameter/field this body is attached to"""
        raise NotImplementedError


class ParameterExtractor(Protocol):
    def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        raise NotImplementedError


class ParameterExtractorMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> ParameterExtractor:
        """Hook to pull information from the Python parameter/field this body is attached to"""
        raise NotImplementedError


class OpenAPIBody(Protocol):
    include_in_schema: bool

    def get_models(self) -> List[type]:
        """The type representing this parameter.

        This is used as the key to deduplicate references and schema names.
        """
        raise NotImplementedError

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.RequestBody:
        raise NotImplementedError

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        raise NotImplementedError

    def get_media_type_string(self) -> str:
        raise NotImplementedError

    def get_openapi_media_type(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.MediaType:
        raise NotImplementedError

    def get_encoding(self) -> Optional[models.Encoding]:
        raise NotImplementedError

    def get_field_name(self) -> str:
        raise NotImplementedError


class OpenAPIBodyMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        raise NotImplementedError


class OpenAPIParameter(Protocol):
    in_: str
    name: str
    include_in_schema: bool

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.ConcreteParameter:
        raise NotImplementedError

    def get_models(self) -> List[type]:
        """Used as the key to deduplicate references and schema names"""
        raise NotImplementedError


class OpenAPIParameterMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> OpenAPIParameter:
        raise NotImplementedError
