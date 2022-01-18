from __future__ import annotations

import inspect
import typing

from di.api.dependencies import DependantBase

from xpresso._extractors.api import (
    BodyExtractor,
    BodyExtractorMarker,
    ParameterExtractor,
    ParameterExtractorMarker,
)
from xpresso._openapi_providers.api import (
    OpenAPIBody,
    OpenAPIBodyMarker,
    OpenAPIParameter,
    OpenAPIParameterMarker,
)
from xpresso.dependencies.models import Dependant


class ParameterDependantMarker(Dependant):
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

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, o: object) -> bool:
        return o is self

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        return ParameterDependant(
            in_=self.in_,
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )


class ParameterDependant(Dependant):
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

    def __hash__(self) -> int:
        # As per the spec, parameters are identified
        # by name and location
        return hash((self.openapi.name, self.in_))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ParameterDependant):
            return self.openapi.name == o.openapi.name and self.in_ == o.in_
        return False


class BodyDependantMarker(Dependant):
    def __init__(
        self,
        *,
        extractor_marker: BodyExtractorMarker,
        openapi_marker: OpenAPIBodyMarker,
    ) -> None:
        super().__init__(call=None, scope="connection")
        self.extractor_marker = extractor_marker
        self.openapi_marker = openapi_marker

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, o: object) -> bool:
        return self is o

    def register_parameter(self, param: inspect.Parameter) -> BodyDependant:
        return BodyDependant(
            openapi=self.openapi_marker.register_parameter(param),
            extractor=self.extractor_marker.register_parameter(param),
        )


class BodyDependant(Dependant):
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
