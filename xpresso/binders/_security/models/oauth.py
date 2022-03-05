import inspect
import typing
from dataclasses import dataclass, replace

from xpresso.binders._security.extractors.oauth import OAuth2ExtractorMarker
from xpresso.binders._security.openapi.oauth import AuthorizationCodeBearerOpenAPI
from xpresso.binders.api import OpenAPISecurityScheme, SecurityExtractor


@dataclass
class OAuth2AuthorizationCodeBearer:
    authorization_url: str
    token_url: str
    scheme_name: typing.Optional[str] = None
    refresh_url: typing.Optional[str] = None
    description: typing.Optional[str] = None
    include_in_schema: bool = True
    scopes: typing.Optional[typing.Mapping[str, str]] = None
    required_scopes: typing.Optional[typing.AbstractSet[str]] = None

    def require_scopes(
        self, scopes: typing.AbstractSet[str]
    ) -> "OAuth2AuthorizationCodeBearer":
        required_scopes = frozenset(*(self.required_scopes or ()), *scopes)
        return replace(self, required_scopes=required_scopes)

    def register_parameter(
        self, param: inspect.Parameter
    ) -> typing.Tuple[SecurityExtractor, OpenAPISecurityScheme]:
        scheme_name = self.scheme_name or self.__class__.__name__
        return (
            OAuth2ExtractorMarker(
                required_scopes=frozenset(self.required_scopes or ())
            ).register_parameter(param),
            AuthorizationCodeBearerOpenAPI(
                scheme_name=scheme_name,
                description=self.description,
                include_in_schema=self.include_in_schema,
                authorization_url=self.authorization_url,
                token_url=self.token_url,
                refresh_url=self.refresh_url,
                scopes=self.scopes or {},
                required_scopes=frozenset(self.required_scopes or ()),
            ).register_parameter(param),
        )
