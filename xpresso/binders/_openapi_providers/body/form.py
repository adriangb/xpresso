import inspect
import sys
import typing
from dataclasses import dataclass

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from di.typing import get_markers_from_parameter

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    ModelNameMap,
    OpenAPIBody,
    OpenAPIBodyMarker,
    Schemas,
)
from xpresso.binders._openapi_providers.body.form_field import OpenAPIFormFieldMarker
from xpresso.binders._openapi_providers.utils import parse_examples
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models as openapi_models


@dataclass(frozen=True)
class OpenAPIFormDataBody(OpenAPIBody):
    field_openapi_providers: typing.Mapping[str, OpenAPIBody]
    required_fields: typing.List[str]
    description: typing.Optional[str]
    examples: typing.Optional[typing.Mapping[str, openapi_models.Example]]
    media_type: Literal[
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    ]
    required: bool
    nullable: bool

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        properties = {
            field_name: field_openapi.get_schema(
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

    def get_media_type_object(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.MediaType:
        encodings: typing.Dict[str, openapi_models.Encoding] = {}
        for field_name, field_openapi in self.field_openapi_providers.items():
            encoding = field_openapi.get_encoding()
            if encoding:
                encodings[field_name] = encoding
        return openapi_models.MediaType(
            schema=self.get_schema(model_name_map=model_name_map, schemas=schemas),
            examples=self.examples,  # type: ignore[arg-type]
            encoding=encodings or None,
        )

    def get_media_type(self) -> str:
        return self.media_type

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


@dataclass(frozen=True)
class OpenAPIFormDataMarker(OpenAPIBodyMarker):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    media_type: Literal[
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    ]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        form_data_field = model_field_from_param(param)
        if form_data_field.required is False:
            required = False
        else:
            required = True

        field_openapi_providers: typing.Dict[str, OpenAPIBody] = {}
        required_fields: typing.List[str] = []
        # use pydantic to get rid of outer annotated, optional, etc.
        annotation = form_data_field.type_
        for field_param in inspect.signature(annotation).parameters.values():
            marker: typing.Optional[BodyBinderMarker] = None
            for param_marker in get_markers_from_parameter(field_param):
                if isinstance(param_marker, BodyBinderMarker):
                    marker = param_marker
                    break
            field_openapi: OpenAPIBodyMarker
            if marker is None:
                # use the defaults
                field_openapi = OpenAPIFormFieldMarker(
                    alias=None,
                    style="form",
                    explode=True,
                )
            else:
                field_openapi = marker.openapi_marker
            provider = field_openapi.register_parameter(field_param)
            field_name = provider.get_field_name()
            field_openapi_providers[field_name] = provider
            field = model_field_from_param(field_param)
            if field.required is not False:
                required_fields.append(field_name)
        examples = parse_examples(self.examples) if self.examples else None
        return OpenAPIFormDataBody(
            field_openapi_providers=field_openapi_providers,
            required_fields=required_fields,
            description=self.description,
            examples=examples,
            media_type=self.media_type,
            required=required,
            nullable=form_data_field.allow_none,
        )
