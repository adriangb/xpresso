import inspect
import typing
from dataclasses import dataclass

import xpresso.openapi.models as openapi_models
from xpresso.binders._security.extractors.apikey import APIKeyExtractorMarker
from xpresso.binders._security.openapi.apikey import APIKeySecurityScheme
from xpresso.binders.api import OpenAPISecurityScheme, SecurityExtractor


@dataclass
class _APIKey:
    param_name: str
    scheme_name: typing.Optional[str] = None
    description: typing.Optional[str] = None
    include_in_schema: bool = True
    in_: typing.ClassVar[openapi_models.APIKeyLocation]

    def register_parameter(
        self, param: inspect.Parameter
    ) -> typing.Tuple[SecurityExtractor, OpenAPISecurityScheme]:
        scheme_name = self.scheme_name or self.__class__.__name__
        return (
            APIKeyExtractorMarker(
                in_=self.in_, name=self.param_name
            ).register_parameter(param),
            APIKeySecurityScheme(
                include_in_schema=self.include_in_schema,
                scheme_name=scheme_name,
                name=self.param_name,
                in_=self.in_,
                description=self.description,
            ).register_parameter(param),
        )


class APIKeyHeader(_APIKey):
    in_: typing.ClassVar[openapi_models.APIKeyLocation] = "header"


class APIKeyQuery(_APIKey):
    in_: typing.ClassVar[openapi_models.APIKeyLocation] = "query"


class APIKeyCookie(_APIKey):
    in_: typing.ClassVar[openapi_models.APIKeyLocation] = "cookie"
