from xpresso.binders._openapi_providers.params.base import (
    OpenAPIParameterBase,
    OpenAPIParameterMarkerBase,
)
from xpresso.openapi import models as openapi_models


class OpenAPICookieParameter(OpenAPIParameterBase):
    param_cls = openapi_models.Cookie


class OpenAPICookieParameterMarker(OpenAPIParameterMarkerBase):
    cls = OpenAPICookieParameter
    in_ = "cookie"
