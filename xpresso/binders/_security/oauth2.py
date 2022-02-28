from __future__ import annotations

from typing import AbstractSet, ClassVar, Mapping, Optional, Protocol

from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso.binders._security.utils import get_authorization_scheme_param
from xpresso.binders.api import SecurityScheme
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)


class _OAuth2Base(SecurityScheme, Protocol):
    scheme_name: ClassVar[Optional[str]] = None
    description: ClassVar[Optional[str]] = None
    unauthorized_error: ClassVar[Optional[Exception]] = UNAUTHORIZED_EXC


UNAUTHORIZED_CHALLANGE_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


class OAuth2AuthorizationCodeBearer(_OAuth2Base, Protocol):
    unauthorized_error: ClassVar[Optional[Exception]] = UNAUTHORIZED_CHALLANGE_EXC
    authorization_url: ClassVar[str]
    token_url: ClassVar[str]
    refresh_url: ClassVar[Optional[str]] = None
    scopes: ClassVar[Optional[Mapping[str, str]]] = None
    required_scopes: ClassVar[Optional[AbstractSet[str]]] = None

    token: str

    def __init__(self, token: str) -> None:
        self.token = token

    @classmethod
    async def extract(
        cls, conn: HTTPConnection
    ) -> Optional[OAuth2AuthorizationCodeBearer]:
        authorization: str = conn.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if cls.unauthorized_error:
                raise cls.unauthorized_error
            else:
                return None
        return cls(param)

    @classmethod
    def get_openapi(cls) -> openapi_models.OAuth2:
        return openapi_models.OAuth2(
            description=cls.description,
            flows=openapi_models.OAuthFlows(
                authorizationCode=openapi_models.OAuthFlowAuthorizationCode(
                    refreshUrl=cls.refresh_url,  # type: ignore[assignment]
                    tokenUrl=cls.token_url,
                    authorizationUrl=cls.authorization_url,
                    scopes=cls.scopes or {},
                )
            ),
        )
