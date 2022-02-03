import inspect
import sys
from typing import Dict, List, Optional, Union

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from xpresso.openapi import models

Model = type
ModelNameMap = Dict[Model, str]
Schemas = Dict[str, Union[models.Schema, models.Reference]]


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


class OpenAPISecurityScheme(Protocol):
    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.SecurityScheme:
        raise NotImplementedError

    def get_models(self) -> List[type]:
        """Used as the key to deduplicate references and schema names"""
        raise NotImplementedError


class OpenAPISecuritySchemeMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> OpenAPISecurityScheme:
        raise NotImplementedError
