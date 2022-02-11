import inspect
import typing

from di import Dependant
from di.api.dependencies import CacheKey, DependantBase

from xpresso.binders.api import (
    BodyExtractor,
    BodyExtractorMarker,
    OpenAPIBody,
    OpenAPIBodyMarker,
    OpenAPIParameter,
    OpenAPIParameterMarker,
    ParameterExtractor,
    ParameterExtractorMarker,
)


class ParameterBinderMarker(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        in_: str,
        extractor_marker: ParameterExtractorMarker,
        openapi_marker: OpenAPIParameterMarker,
    ) -> None:
        super().__init__(call=None, scope="connection")
        self.in_ = in_
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        return ParameterBinder(
            in_=self.in_,
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )


class ParameterBinder(Dependant[typing.Any]):
    __slots__ = (
        "in_",
        "alias",
        "openapi",
    )

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


class BodyBinder(Dependant[typing.Any]):
    __slots__ = ("openapi", "extractor")

    def __init__(
        self,
        *,
        openapi: OpenAPIBody,
        extractor: BodyExtractor,
    ) -> None:
        super().__init__(call=extractor.extract_from_request, scope="connection")
        self.openapi = openapi
        self.extractor = extractor


class BodyBinderMarker(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        extractor_marker: BodyExtractorMarker,
        openapi_marker: OpenAPIBodyMarker,
    ) -> None:
        super().__init__(call=None, scope="connection")
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def register_parameter(self, param: inspect.Parameter) -> BodyBinder:
        return BodyBinder(
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )
