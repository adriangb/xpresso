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
from xpresso.binders._openapi_providers.utils import parse_examples
from xpresso.openapi import models as openapi_models
from xpresso.openapi.constants import REF_PREFIX


@dataclass(frozen=True)
class OpenAPIJsonBody(OpenAPIBody):
    description: typing.Optional[str]
    examples: typing.Optional[typing.Mapping[str, openapi_models.Example]]
    field: ModelField
    required: bool

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
        return openapi_models.Schema(**schema, nullable=self.field.allow_none or None)

    def get_media_type_object(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        return openapi_models.MediaType(
            schema=self.get_schema(model_name_map=model_name_map, schemas=schemas),
            examples=self.examples,  # type: ignore[arg-type]
        )

    def get_media_type(self) -> str:
        return "application/json"

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                "application/json": self.get_media_type_object(model_name_map, schemas)
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
        )
