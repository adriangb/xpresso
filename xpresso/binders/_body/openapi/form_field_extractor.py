import inspect
import typing

from di.typing import get_markers_from_parameter

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import FormFieldOpenAPIProvider
from xpresso.binders.api import ModelNameMap, OpenAPIBody, Schemas
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models

T = typing.TypeVar("T")


class _Base(typing.NamedTuple):
    field_name: str
    include_in_schema: bool
    field_openapi: OpenAPIBody

    def get_models(self) -> typing.List[type]:
        return self.field_openapi.get_models()

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Encoding:
        return self.field_openapi.get_field_encoding(model_name_map, schemas)


class OpenAPIField(_Base):
    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return self.field_openapi.get_field_schema(
            model_name_map=model_name_map, schemas=schemas
        )


class OpenAPIRepeatedField(_Base):
    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return models.Schema(
            type="array",
            items=self.field_openapi.get_field_schema(
                model_name_map=model_name_map, schemas=schemas
            ),
        )


class OpenAPIFieldMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    include_in_schema: bool
    repeated: bool

    def register_parameter(self, param: inspect.Parameter) -> FormFieldOpenAPIProvider:
        for marker in get_markers_from_parameter(param):
            if isinstance(marker, BodyBinderMarker):
                field_marker = marker
                break
        else:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        openapi_provider = field_marker.openapi_marker.register_parameter(param)
        field_name = self.alias or model_field_from_param(param).alias
        if self.repeated:
            return OpenAPIRepeatedField(
                field_name=field_name,
                field_openapi=openapi_provider,
                include_in_schema=self.include_in_schema,
            )
        return OpenAPIField(
            field_name=field_name,
            field_openapi=openapi_provider,
            include_in_schema=self.include_in_schema,
        )
