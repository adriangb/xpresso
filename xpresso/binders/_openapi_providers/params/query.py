from xpresso.binders._openapi_providers.params.base import (
    OpenAPIParameterBase,
    OpenAPIParameterMarkerBase,
)
from xpresso.openapi import models as openapi_models


class OpenAPIQueryParameter(OpenAPIParameterBase):
    param_cls = openapi_models.Query


class OpenAPIQueryParameterMarker(OpenAPIParameterMarkerBase):
    cls = OpenAPIQueryParameter
    in_ = "header"
