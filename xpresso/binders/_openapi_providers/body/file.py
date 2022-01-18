import inspect
import sys
import typing
from dataclasses import dataclass

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    ModelNameMap,
    OpenAPIBody,
    OpenAPIBodyMarker,
    Schemas,
)
from xpresso.binders._openapi_providers.utils import parse_examples
from xpresso.openapi import models as openapi_models


@dataclass(frozen=True)
class OpenAPIFileBody(OpenAPIBody):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[typing.Mapping[str, openapi_models.Example]]
    format: Literal["binary", "base64"]
    required: bool
    nullable: bool

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_models.Schema(
            type="string", format=self.format, nullable=self.nullable or None
        )

    def get_media_type_object(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        return openapi_models.MediaType(
            schema=self.get_schema(model_name_map=model_name_map, schemas=schemas),
            examples=self.examples,  # type: ignore[arg-type]
        )

    def get_media_type(self) -> str:
        return self.media_type or "*/*"

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                self.get_media_type(): self.get_media_type_object(
                    model_name_map, schemas
                )
            },
        )

    def get_encoding(self) -> typing.Optional[openapi_models.Encoding]:
        if self.media_type:
            return openapi_models.Encoding(contentType=self.media_type)
        return None


@dataclass(frozen=True)
class OpenAPIFileMarker(OpenAPIBodyMarker):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    format: Literal["binary", "base64"]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        examples = parse_examples(self.examples) if self.examples else None
        if field.required is False:
            required = False
        else:
            required = True
        return OpenAPIFileBody(
            media_type=self.media_type,
            description=self.description,
            examples=examples,
            format=self.format,
            required=required,
            nullable=field.allow_none,
        )
