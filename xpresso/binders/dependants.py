import inspect
import typing

from di import Dependant, Marker
from di.api.dependencies import CacheKey, DependantBase
from starlette.requests import HTTPConnection

from xpresso._utils.compat import Annotated, get_args, get_origin
from xpresso.binders.api import (
    BodyExtractor,
    OpenAPIBody,
    OpenAPIParameter,
    OpenAPISecurityScheme,
    ParameterExtractor,
    SecurityExtractor,
)
from xpresso.binders.utils import SupportsMarker
from xpresso.dependencies.models import Depends
from xpresso.exceptions import HTTPException


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
        marker: "SecurityBinderMarker",
    ) -> None:
        super().__init__(call=extractor.extract, scope="connection", marker=marker)
        self.extractor = extractor
        self.openapi = openapi

    @property
    def cache_key(self) -> CacheKey:
        if self.openapi.required_scopes is None:
            required_scopes = None
        else:
            required_scopes = frozenset(self.openapi.required_scopes)
        return (self.openapi.scheme_name, required_scopes)


SecuritySchemeMarker = SupportsMarker[
    typing.Tuple[SecurityExtractor, OpenAPISecurityScheme]
]


class SecurityBinderMarker(Depends):
    dependency: typing.Optional[SecuritySchemeMarker]

    def __init__(
        self,
        scheme_marker: typing.Optional[SecuritySchemeMarker] = None,
    ) -> None:
        super().__init__()
        self.dependency = scheme_marker

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        if self.dependency is not None:
            extractor, openapi = self.dependency.register_parameter(param)
            return SecurityBinder(extractor=extractor, openapi=openapi, marker=self)
        annotation = param.annotation
        if get_origin(annotation) is Annotated:
            annotation = next(iter(get_args(annotation)))
        if get_origin(annotation) is typing.Union:
            extractors: typing.List[SecurityExtractor] = []
            optional = False
            for tp in get_args(annotation):
                if tp is None:
                    optional = True
                    continue
                extractors.append(tp)

            async def extract(conn: HTTPConnection) -> typing.Any:
                for extractor in extractors:
                    try:
                        return await extractor.extract(conn)
                    except HTTPException:
                        pass
                if optional:
                    return None
                raise HTTPException(status_code=401, detail="Not authenticated")

            return Dependant(call=extract, marker=self, scope="connection")
        return Depends().register_parameter(param)
