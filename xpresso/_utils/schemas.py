from typing import Any, Dict

from pydantic.fields import ModelField
from pydantic.schema import field_schema

from xpresso._utils.pydantic_utils import filter_pydantic_models_from_mapping
from xpresso.binders.api import ModelNameMap
from xpresso.openapi import models as openapi_models
from xpresso.openapi._constants import REF_PREFIX


def openapi_schema_from_pydantic_field(
    field: ModelField,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> openapi_models.Schema:
    schema, refs, _ = field_schema(
        field,
        by_alias=True,
        ref_prefix=REF_PREFIX,
        model_name_map=filter_pydantic_models_from_mapping(model_name_map),
    )
    schemas.update(refs)
    return openapi_models.Schema(**schema, nullable=field.allow_none or None)
