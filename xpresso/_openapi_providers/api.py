import inspect
import sys
from typing import Any, Dict, Optional

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from pydantic.schema import TypeModelOrEnum

from xpresso.openapi import models

ModelNameMap = Dict[TypeModelOrEnum, str]
Schemas = Dict[str, Any]


class OpenAPIBody(Protocol):
    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.RequestBody:
        raise NotImplementedError

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        raise NotImplementedError

    def get_media_type(self) -> str:
        raise NotImplementedError

    def get_media_type_object(
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

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.ConcreteParameter:
        raise NotImplementedError

    def __eq__(self, o: object) -> bool:
        """Used to de-duplicate parameters declared in multiple places.

        Note that a parameter (defined by in_ and name) should not exist
        more than once with different options.
        This function should take into account _all_ options (e.g. style and explode).
        """
        raise NotImplementedError


class OpenAPIParameterMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> OpenAPIParameter:
        raise NotImplementedError
