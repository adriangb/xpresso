from pydantic.schema import field_schema, get_flat_models_from_field, get_model_name_map

from xpresso.binders._openapi_providers.api import ModelNameMap, Schemas
from xpresso.binders._openapi_providers.params.base import (
    OpenAPIParameterBase,
    OpenAPIParameterMarkerBase,
)
from xpresso.openapi import models as openapi_models
from xpresso.openapi.constants import REF_PREFIX


class OpenAPIHeaderParameter(OpenAPIParameterBase):
    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.ConcreteParameter:
        model_name_map.update(
            get_model_name_map(
                get_flat_models_from_field(
                    self.field,
                    model_name_map.keys(),  # type: ignore[arg-type]
                )
            )
        )
        schema, refs, _ = field_schema(
            self.field,
            by_alias=True,
            ref_prefix=REF_PREFIX,
            model_name_map=model_name_map,
        )
        schemas.update(refs)
        return openapi_models.Header(
            description=self.description or self.field.field_info.description,  # type: ignore[arg-type]
            required=self.required,
            deprecated=self.deprecated,
            style=self.style,  # type: ignore[arg-type]
            explode=self.explode,
            schema=openapi_models.Schema(
                **schema, nullable=self.field.allow_none or None
            ),
            examples=self.examples,  # type: ignore[arg-type]
            name=self.name,
        )


class OpenAPIHeaderParameterMarker(OpenAPIParameterMarkerBase):
    cls = OpenAPIHeaderParameter
    in_ = "header"
