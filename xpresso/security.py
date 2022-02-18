from typing import Any, List, Union, cast

from pydantic import BaseModel
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket

from xpresso.binders._security.apikey import APIKeyCookie as APIKeyCookie  # noqa: F401
from xpresso.binders._security.apikey import APIKeyHeader as APIKeyHeader  # noqa: F401
from xpresso.binders._security.apikey import APIKeyQuery as APIKeyQuery  # noqa: F401
from xpresso.binders._security.oauth import OAuth2 as OAuth2  # noqa: F401
from xpresso.binders._security.oauth import (  # noqa: F401
    OAuth2AuthorizationCodeBearer as OAuth2AuthorizationCodeBearer,
)
from xpresso.binders._security.oauth import (  # noqa: F401
    OAuth2PasswordBearer as OAuth2PasswordBearer,
)
from xpresso.binders._security.oauth import (  # noqa: F401
    OAuth2PasswordRequestForm as OAuth2PasswordRequestForm,
)
from xpresso.binders.api import NamedSecurityScheme
from xpresso.binders.api import SecurityScheme as SecurityScheme  # noqa: F401
from xpresso.dependencies.models import Depends
from xpresso.typing import Annotated

Connection = Annotated[
    Union[Request, WebSocket], Depends(HTTPConnection, scope="connection", wire=False)
]


class SecurityModel(BaseModel, SecurityScheme):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        for field in cls.__fields__.values():
            if not issubclass(field.type_, SecurityScheme):
                raise TypeError(
                    "Fields must be either a SecurityModel or a SecurityScheme"
                )

    @classmethod
    async def __call__(cls, conn: Connection) -> Any:
        return cls(
            **{
                field_name: await cast(SecurityScheme, field.type_).__call__(conn)
                for field_name, field in cls.__fields__.items()
            }
        )

    @classmethod
    def get_openapi(cls) -> List[List[NamedSecurityScheme]]:
        res: List[List[NamedSecurityScheme]] = []
        for field in cls.__fields__.values():
            assert issubclass(field.type_, SecurityScheme)
            openapi = field.type_.get_openapi()
            if isinstance(openapi, list):
                required_schemes: List[NamedSecurityScheme] = []
                for sub in openapi:
                    if isinstance(sub, NamedSecurityScheme):
                        required_schemes.append(sub)
                    # any other relationship cannot be modeled by OpenAPI
                res.append(required_schemes)
            else:
                res.append([openapi])
            if not all(isinstance(oai, NamedSecurityScheme) for oai in openapi):
                raise TypeError
        return res
