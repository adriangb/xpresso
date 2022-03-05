import inspect
import typing

from xpresso.binders.api import OpenAPISecurityScheme
from xpresso.openapi import models as openapi_models


class AuthorizationCodeBearerOpenAPI(typing.NamedTuple):
    scheme_name: str
    description: typing.Optional[str]
    include_in_schema: bool

    authorization_url: str
    token_url: str
    refresh_url: typing.Optional[str]
    scopes: typing.Mapping[str, str]
    required_scopes: typing.AbstractSet[str]

    def get_openapi(self) -> openapi_models.SecurityScheme:
        return openapi_models.OAuth2(
            flows=openapi_models.OAuthFlows(
                authorizationCode=openapi_models.OAuthFlowAuthorizationCode(
                    refreshUrl=self.refresh_url,  # type: ignore[arg-type]
                    scopes=dict(self.scopes),
                    authorizationUrl=self.authorization_url,
                    tokenUrl=self.token_url,
                )
            )
        )

    def register_parameter(self, param: inspect.Parameter) -> OpenAPISecurityScheme:
        return self
