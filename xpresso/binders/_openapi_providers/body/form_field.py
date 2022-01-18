import inspect
import typing
from dataclasses import dataclass

from pydantic.fields import ModelField
from pydantic.schema import field_schema, get_flat_models_from_field, get_model_name_map

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    ModelNameMap,
    OpenAPIBody,
    OpenAPIBodyMarker,
    Schemas,
)
from xpresso.openapi import models as openapi_models
from xpresso.openapi.constants import REF_PREFIX


@dataclass(frozen=True)
class OpenAPIFormField(OpenAPIBody):
    alias: typing.Optional[str]
    style: str
    explode: bool
    name: str
    field: ModelField

    def get_field_name(self) -> str:
        return self.name

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        model_name_map.update(
            get_model_name_map(
                get_flat_models_from_field(
                    self.field,
                    model_name_map.keys(),  # type: ignore[arg-type]
                )
            )
        )
        schema, refs, _ = field_schema(
            self.field,
            by_alias=True,
            ref_prefix=REF_PREFIX,
            model_name_map=model_name_map,
        )
        schemas.update(refs)
        return openapi_models.Schema(**schema)

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

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        name = self.alias or field.alias
        return OpenAPIFormField(
            alias=self.alias,
            style=self.style,
            explode=self.explode,
            name=name,
            field=field,
        )
