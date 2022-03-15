from typing import Any, Optional

from di.dependant import Injectable
from pydantic import BaseModel
from starlette.requests import HTTPConnection

from xpresso.binders._security.apikey import APIKeyHeader
from xpresso.binders._security.oauth2 import OAuth2AuthorizationCodeBearer

__all__ = (
    "APIKeyHeader",
    "OAuth2AuthorizationCodeBearer",
    "RequiredSecuritySchemes",
    "AlternativeSecuritySchemes",
)


class RequiredSecuritySchemes(BaseModel, Injectable):
    def __init_subclass__(cls) -> None:
        return super().__init_subclass__(call=cls.extract, scope="connection")

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Any:
        data = {}
        for field in cls.__fields__.values():
            data[field.name] = await field.type_.extract(conn)
        return cls(**data)

    class Config:
        arbitrary_types_allowed = True


class AlternativeSecuritySchemes(BaseModel, Injectable):
    def __init_subclass__(cls) -> None:
        return super().__init_subclass__(call=cls.extract, scope="connection")

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Any:
        data = {}
        err: Optional[Exception] = None
        for field in cls.__fields__.values():
            try:
                data[field.name] = await field.type_.extract(conn)
            except Exception as e:
                err = e
                data[field.name] = None
        if not any(data.values()) and err:
            raise err
        return cls(**data)

    class Config:
        arbitrary_types_allowed = True
