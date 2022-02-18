from __future__ import annotations

import sys
from typing import AbstractSet, ClassVar, List, Mapping, Optional

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from pydantic import BaseModel
from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso.binders._security.utils import get_authorization_scheme_param
from xpresso.binders.api import NamedSecurityScheme, SecurityScheme
from xpresso.bodies import FormEncodedField
from xpresso.exceptions import HTTPException
from xpresso.typing import Annotated


class OAuth2PasswordRequestForm(BaseModel):
    """
    This is a dependency class, use it like:
        @app.post("/login")
        def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
            data = form_data.parse()
            print(data.username)
            print(data.password)
            for scope in data.scopes:
                print(scope)
            if data.client_id:
                print(data.client_id)
            if data.client_secret:
                print(data.client_secret)
            return data
    It creates the following Form conn parameters in your endpoint:
    grant_type: the OAuth2 spec says it is required and MUST be the fixed string "password".
    username: username string. The OAuth2 spec requires the exact field name "username".
    password: password string. The OAuth2 spec requires the exact field name "password".
    scope: Optional string. Several scopes (each one a string) separated by spaces. E.g.
        "items:read items:write users:read profile openid"
    client_id: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
        using HTTP Basic auth, as: client_id:client_secret
    client_secret: optional string. OAuth2 recommends sending the client_id and client_secret (if any)
        using HTTP Basic auth, as: client_id:client_secret
    """

    username: str
    password: str
    scopes: Annotated[
        List[str], FormEncodedField(style="spaceDelimited", explode=False)
    ]
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    grant_type: Literal["password"]


class OAuth2(SecurityScheme):
    token: str
    description: ClassVar[Optional[str]] = None
    scheme_name: ClassVar[Optional[str]] = None
    unauthenticated_error: ClassVar[Optional[Exception]] = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )

    def __init__(self, token: str) -> None:
        self.token = token

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[OAuth2]:  # type: ignore  # for Pylance
        authorization: Optional[str] = conn.headers.get("Authorization")
        if not authorization:
            if cls.unauthenticated_error:
                raise cls.unauthenticated_error
            else:
                return None
        return OAuth2(token=authorization)

    @classmethod
    def get_openapi(cls) -> NamedSecurityScheme:
        scheme = openapi_models.OAuth2(
            description=cls.description, flows=openapi_models.OAuthFlows()
        )
        return NamedSecurityScheme(
            name=cls.scheme_name or cls.__name__,
            scheme=scheme,
        )


class OAuth2PasswordBearer(OAuth2):
    token_url: str
    scopes: Optional[Mapping[str, str]] = None
    required_scopes: AbstractSet[str] = frozenset()
    unauthenticated_error = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    @classmethod
    def get_openapi(cls) -> NamedSecurityScheme:
        scheme = openapi_models.OAuth2(
            flows=openapi_models.OAuthFlows(
                password=openapi_models.OAuthFlowPassword(
                    scopes=cls.scopes, tokenUrl=cls.token_url
                )
            )
        )
        return NamedSecurityScheme(
            name=cls.scheme_name or cls.__name__,
            scheme=scheme,
        )

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[OAuth2PasswordBearer]:
        authorization: Optional[str] = conn.headers.get("Authorization")
        if authorization:
            scheme, param = get_authorization_scheme_param(authorization)
            if scheme.lower == "bearer":
                return OAuth2PasswordBearer(token=param)
        if cls.unauthenticated_error:
            raise cls.unauthenticated_error
        return None


class OAuth2AuthorizationCodeBearer(OAuth2):
    token_url: ClassVar[str]
    authorization_url: ClassVar[str]
    refresh_url: ClassVar[Optional[str]] = None
    scopes: ClassVar[Optional[Mapping[str, str]]] = None
    required_scopes: ClassVar[Optional[AbstractSet[str]]] = None
    unauthenticated_error: ClassVar[Exception] = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    @classmethod
    def get_openapi(cls) -> NamedSecurityScheme:
        scheme = openapi_models.OAuth2(
            flows=openapi_models.OAuthFlows(
                authorizationCode=openapi_models.OAuthFlowAuthorizationCode(
                    refreshUrl=cls.refresh_url,  # type: ignore[arg-type]
                    scopes=cls.scopes or {},
                    authorizationUrl=cls.authorization_url,
                    tokenUrl=cls.token_url,
                )
            )
        )
        return NamedSecurityScheme(
            name=cls.scheme_name or cls.__name__,
            scheme=scheme,
        )

    @classmethod
    async def extract(
        cls, conn: HTTPConnection
    ) -> Optional[OAuth2AuthorizationCodeBearer]:
        authorization: Optional[str] = conn.headers.get("Authorization")
        if authorization:
            scheme, param = get_authorization_scheme_param(authorization)
            if scheme.lower == "bearer":
                return OAuth2AuthorizationCodeBearer(token=param)
        if cls.unauthenticated_error:
            raise cls.unauthenticated_error
        return None
