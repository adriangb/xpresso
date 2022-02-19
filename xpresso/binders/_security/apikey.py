from __future__ import annotations

from typing import ClassVar, Optional

from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso.binders.api import NamedSecurityScheme, SecurityScheme
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)


class APIKeyBase(SecurityScheme):
    api_key: str
    name: ClassVar[str]
    scheme_name: ClassVar[Optional[str]] = None
    description: ClassVar[Optional[str]] = None
    unauthorized_error: ClassVar[Optional[Exception]] = UNAUTHORIZED_EXC
    in_: ClassVar[str]

    __slots__ = ("api_key",)

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @classmethod
    def get_openapi(cls) -> NamedSecurityScheme:
        scheme = openapi_models.APIKey.parse_obj(
            {
                "in": cls.in_,
                "description": cls.description,
                "name": cls.name,
            }
        )
        return NamedSecurityScheme(
            name=cls.scheme_name or cls.__name__,
            scheme=scheme,
        )


class APIKeyQuery(APIKeyBase):
    in_ = "query"

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[APIKeyQuery]:
        api_key: Optional[str] = conn.query_params.get(cls.name)
        if not api_key:
            if cls.unauthorized_error:
                raise cls.unauthorized_error
            else:
                return None
        return APIKeyQuery(api_key=api_key)


class APIKeyHeader(APIKeyBase):
    in_ = "header"

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[APIKeyHeader]:
        api_key: Optional[str] = conn.headers.get(cls.name)
        if not api_key:
            if cls.unauthorized_error:
                raise cls.unauthorized_error
            else:
                return None
        return APIKeyHeader(api_key=api_key)


class APIKeyCookie(APIKeyBase):
    in_ = "cookie"

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[APIKeyCookie]:
        api_key: Optional[str] = conn.cookies.get(cls.name)
        if not api_key:
            if cls.unauthorized_error:
                raise cls.unauthorized_error
            else:
                return None
        return APIKeyCookie(api_key=api_key)
