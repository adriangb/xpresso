import inspect

from xpresso.binders.api import ModelNameMap, OpenAPIBody, OpenAPIBodyMarker, Schemas
from xpresso.openapi import models


class OpenAPIBodyMsgPack(OpenAPIBody):
    include_in_schema: bool = True

    def get_media_type(self) -> str:
        return "application/x-msgpack"

    def get_media_type_object(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.MediaType:
        return models.MediaType(schema=self.get_schema(model_name_map, schemas))

    def get_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.Schema:
        return models.Schema(
            type="string",
            format="binary",
        )

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> models.RequestBody:
        return models.RequestBody(
            content={
                self.get_media_type(): self.get_media_type_object(
                    model_name_map, schemas
                )
            }
        )


class OpenAPIBodyMarkerMsgPack(OpenAPIBodyMarker):
    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        return OpenAPIBodyMsgPack()
