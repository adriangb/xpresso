from typing import FrozenSet, Iterable, Mapping, NamedTuple, Optional, Union

from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso.binders._security.utils import get_authorization_scheme_param
from xpresso.exceptions import HTTPException
from xpresso.binders.api import SecurityScheme


UNAUTHORIZED_CHALLANGE_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


class OAuth2AuthorizationCodeBearer(SecurityScheme):
    def __init__(
        self,
        scheme_name: str,
        *,
        description: Optional[str] = None,
        authorization_url: str,
        token_url: str,
        refresh_url: Optional[str] = None,
        unauthorized_error: Optional[Exception] = UNAUTHORIZED_CHALLANGE_EXC,
        scopes: Optional[Mapping[str, str]] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.scheme_name = scheme_name
        self.description = description
        self.unauthorized_error = unauthorized_error
        self.scopes = scopes
        self.include_in_schema = include_in_schema
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_url = refresh_url

    async def __call__(self, conn: HTTPConnection) -> Optional[str]:
        authorization: str = conn.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.unauthorized_error:
                raise self.unauthorized_error
            else:
                return None
        return param

    def get_openapi(self) -> openapi_models.OAuth2:
        return openapi_models.OAuth2(
            description=self.description,
            flows=openapi_models.OAuthFlows(
                authorizationCode=openapi_models.OAuthFlowAuthorizationCode(
                    refreshUrl=self.refresh_url,  # type: ignore[assignment]
                    tokenUrl=self.token_url,
                    authorizationUrl=self.authorization_url,
                    scopes=self.scopes or {},
                )
            ),
        )


class OAuth2Token(NamedTuple):
    required_scopes: FrozenSet[str]
    token: str


class RequireScopes(SecurityScheme):
    def __init__(self, model: "Union[SecurityScheme, RequireScopes]", scopes: Iterable[str]) -> None:
        if not isinstance(model, RequireScopes):
            self.model = model
            self.scopes = frozenset(scopes)
            self.include_in_schema = model.include_in_schema
        else:
            self.model = model.model
            self.include_in_schema = model.model.include_in_schema
            self.scopes = frozenset((*scopes, *model.scopes))

    async def __call__(self, conn: HTTPConnection) -> Optional[OAuth2Token]:
        param = await self.model(conn)
        if param is None:
            return None
        return OAuth2Token(self.scopes, param)

    def get_openapi(self) -> openapi_models.SecurityScheme:
        return self.model.get_openapi()

    @property
    def required_scopes(self) -> FrozenSet[str]:
        return self.scopes
