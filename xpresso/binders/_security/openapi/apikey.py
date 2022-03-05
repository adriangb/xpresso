import inspect
import typing

from xpresso._utils.compat import Literal
from xpresso.binders.api import OpenAPISecurityScheme
from xpresso.openapi import models as openapi_models


class APIKeySecurityScheme(typing.NamedTuple):
    include_in_schema: bool
    scheme_name: str
    name: str
    in_: openapi_models.APIKeyLocation
    description: typing.Optional[str]
    required_scopes: Literal[None] = None

    def get_openapi(self) -> openapi_models.SecurityScheme:
        return openapi_models.APIKey(
            description=self.description, name=self.name, in_=self.in_
        )

    def register_parameter(self, param: inspect.Parameter) -> OpenAPISecurityScheme:
        return self
