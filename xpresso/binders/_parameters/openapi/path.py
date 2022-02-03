from dataclasses import dataclass

from xpresso.binders._parameters.openapi.base import (
    OpenAPIParameterBase,
    OpenAPIParameterMarkerBase,
)
from xpresso.openapi import models as openapi_models


class OpenAPIPathParameter(OpenAPIParameterBase):
    param_cls = openapi_models.Path


@dataclass(frozen=True)
class OpenAPIPathParameterMarker(OpenAPIParameterMarkerBase):
    cls = OpenAPIPathParameter
    in_ = "path"
    required = True
