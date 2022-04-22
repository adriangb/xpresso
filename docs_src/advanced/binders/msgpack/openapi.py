import inspect
import typing

from xpresso.binders.api import ModelNameMap, SupportsOpenAPI
from xpresso.openapi import models


class OpenAPI:
    def get_models(self) -> typing.List[type]:
        return []

    def modify_operation_schema(
        self,
        model_name_map: ModelNameMap,
        operation: models.Operation,
        components: models.Components,
    ) -> None:
        operation.requestBody = models.RequestBody(
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


class OpenAPIMarker:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsOpenAPI:
        return OpenAPI()
