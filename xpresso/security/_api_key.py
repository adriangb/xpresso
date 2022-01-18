from typing import Optional

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from xpresso.openapi.models import APIKey
from xpresso.security._base import SecurityBase


class APIKeyBase(SecurityBase):
    pass


class APIKeyQuery(APIKeyBase):
    def __init__(
        self,
        *,
        name: str,
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
        auto_error: bool = True
    ):
        self.model: APIKey = APIKey(
            **{"in": "query"}, name=name, description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        api_key: str = request.query_params.get(self.model.name)
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            else:
                return None
        return api_key


class APIKeyHeader(APIKeyBase):
    def __init__(
        self,
        *,
        name: str,
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
        auto_error: bool = True
    ):
        self.model: APIKey = APIKey(
            **{"in": "header"}, name=name, description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        api_key: str = request.headers.get(self.model.name)
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            else:
                return None
        return api_key


class APIKeyCookie(APIKeyBase):
    def __init__(
        self,
        *,
        name: str,
        scheme_name: Optional[str] = None,
        description: Optional[str] = None,
        auto_error: bool = True
    ):
        self.model: APIKey = APIKey(
            **{"in": "cookie"}, name=name, description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        api_key = request.cookies.get(self.model.name)
        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            else:
                return None
        return api_key
