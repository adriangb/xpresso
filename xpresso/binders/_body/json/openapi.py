import inspect
import typing

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import (
    ModelNameMap,
    Schemas,
    SupportsOpenAPIBody,
    SupportsOpenAPIField,
)
from xpresso.openapi import models as openapi_models


class _BodyOpenAPI(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    field: ModelField
    required: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                "application/json": openapi_models.MediaType(
                    schema=openapi_schema_from_pydantic_field(
                        self.field, model_name_map, schemas
                    ),
                    examples=self.examples,
                )
            },
        )


class _FieldOpenAPI(typing.NamedTuple):
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
        return openapi_models.Encoding(contentType="application/json")


class BodyOpenAPIMarker(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIBody:
        examples = parse_examples(self.examples) if self.examples else None
        field = model_field_from_param(param)
        required = field.required is not False
        return _BodyOpenAPI(
            description=self.description,
            examples=examples,
            field=field,
            required=required,
            include_in_schema=self.include_in_schema,
        )


class FieldOpenAPIMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIField:
        return _FieldOpenAPI(model_field_from_param(param))
