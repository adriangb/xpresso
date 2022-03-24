import inspect
import typing

from di.api.dependencies import CacheKey
from di.dependant import Dependant, Marker

from xpresso._utils.typing import Protocol
from xpresso.binders.api import SupportsExtractor, SupportsOpenAPI

T = typing.TypeVar("T", covariant=True)


class SupportsMarker(Protocol[T]):
    def register_parameter(self, param: inspect.Parameter) -> T:
        ...


class Binder(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        openapi: SupportsOpenAPI,
        extractor: SupportsExtractor,
    ) -> None:
        super().__init__(call=extractor.extract, scope="connection")
        self.openapi = openapi
        self.extractor = extractor

    @property
    def cache_key(self) -> CacheKey:
        return self.extractor


class BinderMarker(Marker):
    def __init__(
        self,
        *,
        extractor_marker: SupportsMarker[SupportsExtractor],
        openapi_marker: SupportsMarker[SupportsOpenAPI],
    ) -> None:
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def register_parameter(self, param: inspect.Parameter) -> Binder:
        return Binder(
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )
