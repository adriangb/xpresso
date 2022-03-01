from dataclasses import dataclass
from typing import ClassVar, Optional, TypeVar

from starlette.requests import HTTPConnection
from starlette.status import HTTP_401_UNAUTHORIZED

import xpresso.openapi.models as openapi_models
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)

T = TypeVar("T")


@dataclass(eq=False)
class _APIKeyBase:
    name: str
    scheme_name: Optional[str] = None
    description: Optional[str] = None
    unauthorized_error: Optional[Exception] = UNAUTHORIZED_EXC
    include_in_schema: bool = True
    _in: ClassVar[openapi_models.APIKeyLocation]
    scopes = None

    def get_openapi(self) -> openapi_models.APIKey:
        return openapi_models.APIKey(
            description=self.description, name=self.name, in_=self._in
        )


class APIKeyHeader(_APIKeyBase):
    _in: ClassVar[openapi_models.APIKeyLocation] = "header"

    async def __call__(self, conn: HTTPConnection) -> Optional[str]:
        api_key: Optional[str] = conn.headers.get(self.name)
        if not api_key:
            if self.unauthorized_error:
                raise self.unauthorized_error
            else:
                return None
        return api_key
