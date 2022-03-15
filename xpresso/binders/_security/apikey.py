from __future__ import annotations

from typing import ClassVar, Optional, TypeVar

from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso._utils.compat import Protocol
from xpresso.binders.api import SecurityScheme
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)

T = TypeVar("T")


class _APIKeyBase(SecurityScheme, Protocol):
    name: ClassVar[str]
    scheme_name: ClassVar[Optional[str]]
    description: ClassVar[Optional[str]] = None
    unauthorized_error: ClassVar[Optional[Exception]] = UNAUTHORIZED_EXC
    in_: ClassVar[openapi_models.APIKeyLocation]

    __slots__ = ("api_key",)

    api_key: str

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @classmethod
    def get_openapi(cls) -> openapi_models.APIKey:
        return openapi_models.APIKey(
            description=cls.description, name=cls.name, in_=cls.in_
        )


class APIKeyHeader(_APIKeyBase, Protocol):
    in_: ClassVar[openapi_models.APIKeyLocation] = "header"
    __slots__ = ()

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Optional[APIKeyHeader]:
        api_key: Optional[str] = conn.headers.get(cls.name)
        if not api_key:
            if cls.unauthorized_error:
                raise cls.unauthorized_error
            else:
                return None
        return cls(api_key=api_key)
