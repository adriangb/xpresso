import inspect
import typing

from xpresso.binders.api import ModelNameMap, OpenAPIBody, Schemas
from xpresso.openapi import models


class OpenAPIBodyMsgPack:
    include_in_schema: bool = True
    media_type = "application/x-msgpack"

    def get_models(self) -> typing.List[type]:
        return []

    def get_openapi_media_type(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.MediaType:
        return models.MediaType(
            schema=self.get_field_schema(model_name_map, schemas)
        )

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return models.Schema(
            type="string",
            format="binary",
        )

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.RequestBody:
        return models.RequestBody(
            content={
                self.media_type: self.get_openapi_media_type(
                    model_name_map, schemas
                )
            }
        )

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Encoding:
        return models.Encoding(contentType=self.media_type)


class OpenAPIBodyMarkerMsgPack:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> OpenAPIBody:
        return OpenAPIBodyMsgPack()
