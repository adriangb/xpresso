import inspect
import typing

from xpresso._utils.compat import Literal
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import ModelNameMap, OpenAPIBody, Schemas
from xpresso.openapi import models as openapi_models


class OpenAPIFileBody(typing.NamedTuple):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    format: Literal["binary", "base64"]
    required: bool
    nullable: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return []

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_models.Schema(
            type="string", format=self.format, nullable=self.nullable or None
        )

    def get_openapi_media_type(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        return openapi_models.MediaType(
            schema=self.get_field_schema(
                model_name_map=model_name_map, schemas=schemas
            ),
            examples=self.examples,  # type: ignore[arg-type]
        )

    def get_media_type_string(self) -> str:
        return self.media_type or "*/*"

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                self.get_media_type_string(): self.get_openapi_media_type(
                    model_name_map, schemas
                )
            },
        )

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        return openapi_models.Encoding(contentType=self.media_type)


class OpenAPIFileMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    format: Literal["binary", "base64"]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        examples = parse_examples(self.examples) if self.examples else None
        required = field.required is not False
        return OpenAPIFileBody(
            media_type=self.media_type,
            description=self.description,
            examples=examples,
            format=self.format,
            required=required,
            nullable=field.allow_none,
            include_in_schema=self.include_in_schema,
        )
