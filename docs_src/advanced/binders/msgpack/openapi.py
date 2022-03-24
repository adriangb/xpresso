import inspect
import typing

from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIMetadata,
    SupportsOpenAPI,
)
from xpresso.openapi import models


class OpenAPI:
    def get_models(self) -> typing.List[type]:
        return []

    def get_openapi(
        self, model_name_map: ModelNameMap
    ) -> OpenAPIMetadata:
        return OpenAPIMetadata(
            body=models.RequestBody(
                content={
                    "application/x-msgpack": models.MediaType(
                        schema=models.Schema(  # type: ignore[arg-type]
                            type="string",
                            format="binary",
                        )
                    )
                },
                required=True,
            )
        )


class OpenAPIMarker:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsOpenAPI:
        return OpenAPI()
