import inspect
import typing

from di.typing import get_markers_from_annotation

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import SupportsXpressoFormDataFieldOpenAPI
from xpresso.binders.api import ModelNameMap, Schemas, SupportsOpenAPIField
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models


class _Base(typing.NamedTuple):
    field_name: str
    include_in_schema: bool
    field_openapi: SupportsOpenAPIField

    def get_models(self) -> typing.List[type]:
        return self.field_openapi.get_models()

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Encoding:
        return self.field_openapi.get_field_encoding(model_name_map, schemas)


class _FieldOpenAPI(_Base):
    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return self.field_openapi.get_field_schema(
            model_name_map=model_name_map, schemas=schemas
        )


class _RepeatedFieldOpenAPI(_Base):
    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return models.Schema(
            type="array",
            items=self.field_openapi.get_field_schema(
                model_name_map=model_name_map, schemas=schemas
            ),
        )


class FieldOpenAPIMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    include_in_schema: bool
    repeated: bool

    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldOpenAPI:
        marker = next(
            get_markers_from_annotation(param.annotation, BodyBinderMarker), None
        )
        if marker is None:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        if marker.openapi_field_marker is None:
            raise TypeError(f"The field {param.name} is not valid as a form field")
        openapi_provider = marker.openapi_field_marker.register_parameter(param)
        field_name = self.alias or model_field_from_param(param).alias
        if self.repeated:
            return _RepeatedFieldOpenAPI(
                field_name=field_name,
                field_openapi=openapi_provider,
                include_in_schema=self.include_in_schema,
            )
        return _FieldOpenAPI(
            field_name=field_name,
            field_openapi=openapi_provider,
            include_in_schema=self.include_in_schema,
        )
