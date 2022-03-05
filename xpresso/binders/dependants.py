import inspect
import typing

from di import Dependant, Marker
from di.api.dependencies import CacheKey, DependantBase

from xpresso.binders.api import (
    BodyExtractor,
    OpenAPIBody,
    OpenAPIParameter,
    OpenAPISecurityScheme,
    ParameterExtractor,
    SecurityExtractor,
)
from xpresso.binders.utils import SupportsMarker


class ParameterBinder(Dependant[typing.Any]):
    def __init__(
        self,
        in_: str,
        openapi: OpenAPIParameter,
        extractor: ParameterExtractor,
    ):
        self.in_ = in_
        self.openapi = openapi
        super().__init__(call=extractor.extract, scope="connection")

    @property
    def cache_key(self) -> CacheKey:
        # As per the spec, parameters are identified
        # by name and location
        return (self.__class__, self.openapi.name, self.in_)


class ParameterBinderMarker(Marker):
    def __init__(
        self,
        *,
        in_: str,
        extractor_marker: SupportsMarker[ParameterExtractor],
        openapi_marker: SupportsMarker[OpenAPIParameter],
    ) -> None:
        self.in_ = in_
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        return ParameterBinder(
            in_=self.in_,
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )


class BodyBinder(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        openapi: OpenAPIBody,
        extractor: BodyExtractor,
    ) -> None:
        super().__init__(call=extractor.extract_from_request, scope="connection")
        self.openapi = openapi
        self.extractor = extractor

    @property
    def cache_key(self) -> CacheKey:
        # Treat each body as unique since there should only be one body
        return (self.__class__, id(self))


class BodyBinderMarker(Marker):
    def __init__(
        self,
        *,
        extractor_marker: SupportsMarker[BodyExtractor],
        openapi_marker: SupportsMarker[OpenAPIBody],
    ) -> None:
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def register_parameter(self, param: inspect.Parameter) -> BodyBinder:
        return BodyBinder(
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )


class SecurityBinder(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        openapi: OpenAPISecurityScheme,
        extractor: SecurityExtractor,
    ) -> None:
        super().__init__(call=extractor.extract, scope="connection")  # type: ignore[arg-type]
        self.openapi = openapi
        self.extractor = extractor

    @property
    def cache_key(self) -> CacheKey:
        if self.openapi.required_scopes is None:
            required_scopes = None
        else:
            required_scopes = frozenset(self.openapi.required_scopes)
        return (self.openapi.scheme_name, required_scopes)


SecurityScheme = SupportsMarker[typing.Tuple[SecurityExtractor, OpenAPISecurityScheme]]


class SecurityBinderMarker(Marker):
    def __init__(
        self,
        scheme: SecurityScheme,
    ) -> None:
        self.scheme = scheme

    def register_parameter(self, param: inspect.Parameter) -> SecurityBinder:
        extractor, openapi = self.scheme.register_parameter(param)
        return SecurityBinder(openapi=openapi, extractor=extractor)
