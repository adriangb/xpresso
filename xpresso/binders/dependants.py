import inspect
import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import get_args
else:
    from typing import get_args

from di import Dependant, Marker
from di.api.dependencies import CacheKey, DependantBase

from xpresso.binders.api import (
    BodyExtractor,
    BodyExtractorMarker,
    NamedSecurityScheme,
    OpenAPIBody,
    OpenAPIBodyMarker,
    OpenAPIParameter,
    OpenAPIParameterMarker,
    ParameterExtractor,
    ParameterExtractorMarker,
    SecurityScheme,
)


class ParameterBinderMarker(Marker):
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


class BodyBinderMarker(Marker):
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


class SecurityBinder(Dependant[typing.Any]):
    def __init__(
        self,
        *,
        scheme_or_model: typing.Type[SecurityScheme],
    ) -> None:
        super().__init__(call=scheme_or_model.extract, scope="connection")
        self.scheme_or_model = scheme_or_model

    @property
    def cache_key(self) -> CacheKey:
        # if this is a single security scheme, we can identify it by name
        oai = self.scheme_or_model.get_openapi()
        if isinstance(oai, NamedSecurityScheme):
            return oai.name
        # otherwise, we identiy the SecurityModel class
        som = self.scheme_or_model

        class CK:
            def __hash__(self) -> int:
                return hash(som)

            def __eq__(self, __o: object) -> bool:
                return __o is som

        return CK()


class SecurityBinderMarker(Dependant[typing.Any]):
    def __init__(self) -> None:
        super().__init__(call=None, scope="connection")

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        scheme_or_model = next(iter(get_args(param.annotation)))
        return SecurityBinder(scheme_or_model=scheme_or_model)
