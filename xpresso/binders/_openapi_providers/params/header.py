from xpresso.binders._openapi_providers.params.base import (
    OpenAPIParameterBase,
    OpenAPIParameterMarkerBase,
)
from xpresso.openapi import models as openapi_models


class OpenAPIHeaderParameter(OpenAPIParameterBase):
    param_cls = openapi_models.Header


class OpenAPIHeaderParameterMarker(OpenAPIParameterMarkerBase):
    cls = OpenAPIHeaderParameter
    in_ = "header"
