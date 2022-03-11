import inspect
import typing

from xpresso._utils.compat import Literal, get_args
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import (
    FormFieldMarker,
    SupportsXpressoFormDataFieldOpenAPI,
)
from xpresso.binders._body.forms.form_encoded_openapi import FormEncodedOpenAPIMarker
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import ModelNameMap, Schemas, SupportsOpenAPIBody
from xpresso.openapi import models as openapi_models


class _BodyOpenAPI(typing.NamedTuple):
    field_openapi_providers: typing.Mapping[str, SupportsXpressoFormDataFieldOpenAPI]
    required_fields: typing.List[str]
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    media_type: Literal[
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    ]
    required: bool
    nullable: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return [
            model
            for provider in self.field_openapi_providers.values()
            for model in provider.get_models()
        ]

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        properties = {
            field_name: field_openapi.get_field_schema(
                model_name_map=model_name_map, schemas=schemas
            )
            for field_name, field_openapi in self.field_openapi_providers.items()
        }
        return openapi_models.Schema(
            type="object",
            properties=properties,
            required=self.required_fields or None,
            nullable=self.nullable or None,
        )

    def get_openapi_media_type(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        encodings: typing.Dict[str, openapi_models.Encoding] = {}
        for field_name, field_openapi in self.field_openapi_providers.items():
            encoding = field_openapi.get_field_encoding(model_name_map, schemas)
            encodings[field_name] = encoding
        return openapi_models.MediaType(
            schema=self.get_schema(model_name_map=model_name_map, schemas=schemas),
            examples=self.examples,  # type: ignore[arg-type]
            encoding=encodings or None,
        )

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                self.media_type: self.get_openapi_media_type(model_name_map, schemas)
            },
        )


class BodyOpenAPIMarker(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    media_type: Literal[
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    ]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIBody:
        form_data_field = model_field_from_param(param)
        required = form_data_field.required is not False
        field_openapi_providers: typing.Dict[
            str, SupportsXpressoFormDataFieldOpenAPI
        ] = {}
        required_fields: typing.List[str] = []
        # use pydantic to get rid of outer annotated, optional, etc.
        model = form_data_field.type_
        for field_param in inspect.signature(model).parameters.values():
            for m in get_args(field_param.annotation):
                if isinstance(m, FormFieldMarker):
                    field_openapi = m.openapi_marker.register_parameter(field_param)
                    break
            else:
                field_openapi = FormEncodedOpenAPIMarker(
                    alias=None,
                    style="form",
                    explode=True,
                    include_in_schema=True,
                ).register_parameter(field_param)
            field_name = field_openapi.field_name
            if field_openapi.include_in_schema:
                field_openapi_providers[field_name] = field_openapi
                field = model_field_from_param(field_param)
                if field.required is not False:
                    required_fields.append(field_name)
        examples = parse_examples(self.examples) if self.examples else None
        return _BodyOpenAPI(
            field_openapi_providers=field_openapi_providers,
            required_fields=required_fields,
            description=self.description,
            examples=examples,
            media_type=self.media_type,
            required=required,
            nullable=form_data_field.allow_none,
            include_in_schema=self.include_in_schema,
        )
