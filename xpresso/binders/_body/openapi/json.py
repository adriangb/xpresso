import inspect
import typing
from dataclasses import dataclass

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import ModelNameMap, OpenAPIBody, OpenAPIBodyMarker, Schemas
from xpresso.openapi import models as openapi_models


@dataclass(frozen=True)
class OpenAPIJsonBody(OpenAPIBody):
    description: typing.Optional[str]
    examples: typing.Optional[typing.Mapping[str, openapi_models.Example]]
    field: ModelField
    required: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_schema_from_pydantic_field(self.field, model_name_map, schemas)

    def get_openapi_media_type(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        return openapi_models.MediaType(
            schema=self.get_schema(model_name_map=model_name_map, schemas=schemas),
            examples=self.examples,  # type: ignore[arg-type]
        )

    def get_media_type_string(self) -> str:
        return "application/json"

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                "application/json": self.get_openapi_media_type(model_name_map, schemas)
            },
        )

    def get_encoding(self) -> openapi_models.Encoding:
        return openapi_models.Encoding(contentType="application/json")


@dataclass(frozen=True)
class OpenAPIJsonMarker(OpenAPIBodyMarker):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        examples = parse_examples(self.examples) if self.examples else None
        field = model_field_from_param(param)
        if field.required is False:
            required = False
        else:
            required = True
        return OpenAPIJsonBody(
            description=self.description,
            examples=examples,
            field=field,
            required=required,
            include_in_schema=self.include_in_schema,
        )
