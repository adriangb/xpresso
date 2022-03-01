import inspect
from typing import Annotated, Any, Awaitable, Callable, Dict, Generic, Iterable, List, Mapping, Type, TypeVar, Union, cast

from di import Marker, Dependant
from di.dependant import Injectable
from di.typing import get_markers_from_parameter
from pydantic import BaseModel
from starlette.requests import HTTPConnection

import xpresso.openapi.models as openapi_models
from xpresso.binders.api import SecurityScheme
from xpresso.binders._security.apikey import APIKeyHeader
from xpresso.binders._security.oauth2 import OAuth2AuthorizationCodeBearer, RequireScopes, OAuth2Token
from xpresso._utils.compat import get_args, get_origin
from xpresso.typing import Annotated


__all__ = (
    "APIKeyHeader",
    "OAuth2AuthorizationCodeBearer",
    "RequireScopes",
    "OAuth2Token",
)


class SecurityModel(BaseModel, Injectable):
    def __init_subclass__(cls) -> None:
        models: Dict[str, SecurityScheme] = {}
        for field_name, field in cls.__fields__.items():
            param = inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=inspect.Parameter.empty if field.required else field.get_default(),
                annotation=param.annotation
            )
            model = get_markers_from_parameter(field)
        async def extract(conn: HTTPConnection) -> SecurityModel:
            return cls(
                **{
                    field_name: await 
                }
            )
        return super().__init_subclass__(call=cls, scope="connection")
    
    @classmethod
    async def extract(cls):

    
    def get_openapi(self) -> Mapping[str, openapi_models.SecurityScheme]:
        models = [cast(SecurityScheme, field.type_) for field in self.__fields__.values()]
        return {model.scheme_name: model.get_openapi() for model in models}

    class Config:
        arbitrary_types_allowed = True


_T = TypeVar("_T")


class _SecurityModelUnion:
    __slots__ = ("models",)
    def __init__(self, models: Iterable[Union[Type[SecurityModel], SecurityScheme]], param: inspect.Parameter) -> None:
        self.models: List[Callable[[HTTPConnection], Awaitable[Any]]] = []
        for model in models:
            if inspect.isclass(model) and issubclass(model, SecurityModel):
                dep = Marker(model).register_parameter(param).call
                async def extract() -> SecurityModel:
                    return 
                self.models.append(model.__call__)
            
                

    def get_openapi(self) -> List[Mapping[str, openapi_models.SecurityScheme]]:
        res: List[Mapping[str, openapi_models.SecurityScheme]] = []
        for model in self.models:
            if isinstance(model, SecurityModel):
                res.append(model.get_openapi())
            else:
                res.append({model.scheme_name: model.get_openapi()})
        return res

    async def __call__(self, conn: HTTPConnection) -> Any:
        errors: List[Exception] = []
        for model in self.models:
            try:
                return await model(conn)


    def __init_subclass__(cls) -> None:
        return super().__init_subclass__(call=cls., scope="connection")

class _SecurityModelUnionMarker(Marker):
    def register_parameter(self, param: inspect.Parameter) -> Dependant:
        return _SecurityModelUnion(param)

SecurityModelUnion = Annotated[_T, "foo"]