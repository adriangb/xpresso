import inspect
import typing
from dataclasses import dataclass

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import model_field_from_param
from xpresso.binders.api import ModelNameMap, OpenAPIBody, OpenAPIBodyMarker, Schemas
from xpresso.openapi import models as openapi_models


@dataclass(frozen=True)
class OpenAPIFormField(OpenAPIBody):
    alias: typing.Optional[str]
    style: str
    explode: bool
    name: str
    field: ModelField
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_field_name(self) -> str:
        return self.name

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_schema_from_pydantic_field(self.field, model_name_map, schemas)

    def get_encoding(self) -> typing.Optional[openapi_models.Encoding]:
        return openapi_models.Encoding(
            contentType=None,
            style=self.style,
            explode=self.explode,
        )


@dataclass(frozen=True)
class OpenAPIFormFieldMarker(OpenAPIBodyMarker):
    alias: typing.Optional[str]
    style: str
    explode: bool
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        name = self.alias or field.alias
        return OpenAPIFormField(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            name=name,
            field=field,
            include_in_schema=self.include_in_schema,
        )
