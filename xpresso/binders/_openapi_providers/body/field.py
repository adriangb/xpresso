import inspect
import typing
from dataclasses import dataclass

from di.typing import get_markers_from_parameter

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    ModelNameMap,
    OpenAPIBody,
    OpenAPIBodyMarker,
    Schemas,
)
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models


@dataclass(frozen=True)
class FieldOpenAPIBase(OpenAPIBody):
    name: str
    field_openapi: OpenAPIBody

    def get_encoding(self) -> typing.Optional[models.Encoding]:
        return self.field_openapi.get_encoding()

    def get_field_name(self) -> str:
        return self.name


class OpenAPIField(FieldOpenAPIBase):
    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return self.field_openapi.get_schema(
            model_name_map=model_name_map, schemas=schemas
        )


class OpenAPIRepeatedField(FieldOpenAPIBase):
    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return models.Schema(
            type="array",
            items=self.field_openapi.get_schema(
                model_name_map=model_name_map, schemas=schemas
            ),
        )


@dataclass(frozen=True)
class OpenAPIFieldMarkerBase(OpenAPIBodyMarker):
    alias: typing.Optional[str]
    cls: typing.ClassVar[
        typing.Union[typing.Type[OpenAPIRepeatedField], typing.Type[OpenAPIField]]
    ]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field_marker: typing.Optional[OpenAPIBodyMarker] = None
        for marker in get_markers_from_parameter(param):
            if isinstance(marker, BodyBinderMarker):
                if marker.openapi_marker is not self:
                    # the outermost marker must be the field marker (us)
                    # so the first one that isn't us is the inner marker
                    field_marker = marker.openapi_marker
        if field_marker is None:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        field_openapi = field_marker.register_parameter(param)
        name = self.alias or model_field_from_param(param).alias
        return self.cls(name=name, field_openapi=field_openapi)


class OpenAPIFieldMarker(OpenAPIFieldMarkerBase):
    cls = OpenAPIField


class OpenAPIRepeatedFieldMarker(OpenAPIFieldMarkerBase):
    cls = OpenAPIRepeatedField
