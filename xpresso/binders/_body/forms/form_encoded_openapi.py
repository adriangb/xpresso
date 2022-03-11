import inspect
import typing

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import SupportsXpressoFormDataFieldOpenAPI
from xpresso.binders.api import ModelNameMap, Schemas
from xpresso.openapi import models as openapi_models


class _FormEncodedOpenAPI(typing.NamedTuple):
    field_name: str
    include_in_schema: bool
    alias: typing.Optional[str]
    style: str
    explode: bool
    field: ModelField

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_schema_from_pydantic_field(self.field, model_name_map, schemas)

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        return openapi_models.Encoding(
            contentType=None,
            style=self.style,
            explode=self.explode,
        )


class FormEncodedOpenAPIMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool
    include_in_schema: bool

    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldOpenAPI:
        field = model_field_from_param(param)
        field_name = self.alias or field.alias
        return _FormEncodedOpenAPI(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            field_name=field_name,
            field=field,
            include_in_schema=self.include_in_schema,
        )
