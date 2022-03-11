import inspect
import typing

from xpresso._utils.compat import Literal
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import (
    ModelNameMap,
    Schemas,
    SupportsOpenAPIBody,
    SupportsOpenAPIField,
)
from xpresso.openapi import models as openapi_models


class OpenAPIFileBody(typing.NamedTuple):
    media_type: str
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    format: Literal["binary", "base64"]
    required: bool
    nullable: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return []

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                self.media_type: openapi_models.MediaType(
                    schema=openapi_models.Schema(
                        type="string",
                        format=self.format,
                        nullable=self.nullable or None,
                    ),
                    examples=self.examples,  # type: ignore[arg-type]
                )
            },
        )


class OpenAPIFileField(typing.NamedTuple):
    media_type: typing.Optional[str]
    format: Literal["binary", "base64"]
    nullable: bool

    def get_models(self) -> typing.List[type]:
        return []

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        return openapi_models.Schema(
            type="string", format=self.format, nullable=self.nullable or None
        )

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        return openapi_models.Encoding(contentType=self.media_type)


class BodyOpenAPIMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    format: Literal["binary", "base64"]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIBody:
        field = model_field_from_param(param)
        examples = parse_examples(self.examples) if self.examples else None
        required = field.required is not False
        return OpenAPIFileBody(
            media_type=self.media_type or "*/*",
            description=self.description,
            examples=examples,
            format=self.format,
            required=required,
            nullable=field.allow_none,
            include_in_schema=self.include_in_schema,
        )


class FieldOpenAPIMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    format: Literal["binary", "base64"]

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIField:
        return OpenAPIFileField(
            media_type=self.media_type,
            format=self.format,
            nullable=model_field_from_param(param).allow_none,
        )
