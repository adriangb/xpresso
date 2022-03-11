import inspect
import typing

from di.api.dependencies import CacheKey, DependantBase
from di.dependant import Dependant, Marker

from xpresso._utils.compat import Protocol
from xpresso.binders.api import (
    SupportsBodyExtractor,
    SupportsExtractor,
    SupportsFieldExtractor,
    SupportsOpenAPIBody,
    SupportsOpenAPIField,
    SupportsOpenAPIParameter,
)

T = typing.TypeVar("T", covariant=True)


class SupportsMarker(Protocol[T]):
    def register_parameter(self, param: inspect.Parameter) -> T:
        ...


class ParameterBinder(Dependant[typing.Any]):
    def __init__(
        self,
        in_: str,
        openapi: SupportsOpenAPIParameter,
        extractor: SupportsExtractor,
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
        extractor_marker: SupportsMarker[SupportsExtractor],
        openapi_marker: SupportsMarker[SupportsOpenAPIParameter],
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
        openapi: typing.Optional[SupportsOpenAPIBody],
        extractor: SupportsBodyExtractor,
    ) -> None:
        super().__init__(call=extractor.extract, scope="connection")
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
        extractor_marker: typing.Optional[SupportsMarker[SupportsBodyExtractor]],
        field_extractor_marker: typing.Optional[SupportsMarker[SupportsFieldExtractor]],
        openapi_marker: typing.Optional[SupportsMarker[SupportsOpenAPIBody]],
        openapi_field_marker: typing.Optional[SupportsMarker[SupportsOpenAPIField]],
    ) -> None:
        self.field_extractor_marker = field_extractor_marker
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker
        self.openapi_field_marker = openapi_field_marker

    def register_parameter(self, param: inspect.Parameter) -> BodyBinder:
        openapi = (
            None
            if self.openapi_marker is None
            else self.openapi_marker.register_parameter(param)
        )
        if self.extractor_marker is None:
            raise TypeError("Top-level bodies MUST provide an extractor implementation")
        return BodyBinder(
            openapi=openapi,
            extractor=self.extractor_marker.register_parameter(param),
        )
