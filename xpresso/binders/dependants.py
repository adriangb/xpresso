import inspect
import typing

from di import Dependant
from di.api.dependencies import CacheKey, DependantBase, MarkerBase

from xpresso._utils.compat import Protocol
from xpresso.binders.api import (
    BodyExtractor,
    OpenAPIBody,
    OpenAPIParameter,
    ParameterExtractor,
)

T = typing.TypeVar("T", covariant=True)


class SupportsMarker(Protocol[T]):
    def register_parameter(self, param: inspect.Parameter) -> T:
        ...


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


class ParameterBinderMarker(MarkerBase):
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


class BodyBinderMarker(MarkerBase):
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
