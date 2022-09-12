import inspect
import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import get_args
else:
    from typing import get_args

import msgspec

from xpresso.binders.api import ModelNameMap, SupportsOpenAPI
from xpresso.openapi import models


class OpenAPI(typing.NamedTuple):
    model: type

    def get_models(self) -> typing.List[type]:
        return [self.model]

    def modify_operation_schema(
        self,
        model_name_map: ModelNameMap,
        operation: models.Operation,
        components: models.Components,
    ) -> None:
        operation.requestBody = (
            operation.requestBody or models.RequestBody(content={})
        )
        if not isinstance(
            operation.requestBody, models.RequestBody
        ):  # pragma: no cover
            raise ValueError(
                "Expected request body to be a RequestBody object, found a reference"
            )
        (schema, *_), schemas = msgspec.json.schema_components(
            [self.model], ref_template="#/components/schemas/{name}"
        )
        operation.requestBody.content[
            "application/json"
        ] = models.MediaType(
            schema=schema,  # type: ignore[arg-type]
        )
        if schemas:
            components.schemas = components.schemas or {}
            components.schemas.update(schemas)


class OpenAPIMarker:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsOpenAPI:
        # get the first parameter to Annotated, which should be our actual type
        model = next(iter(get_args(param.annotation)))
        return OpenAPI(model)
