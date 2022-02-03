import inspect
import typing

from di import BaseContainer, Dependant, SyncExecutor
from di.api.dependencies import CacheKey, DependantBase

import xpresso.openapi.models as openapi_models
from xpresso.binders.api import (
    BodyExtractor,
    BodyExtractorMarker,
    OpenAPIBody,
    OpenAPIBodyMarker,
    OpenAPIParameter,
    OpenAPIParameterMarker,
    ParameterExtractor,
    ParameterExtractorMarker,
    SecurityBase,
)
from xpresso.exceptions import XpressoError


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


class SecurityBinder(Dependant[typing.Any]):
    _model: typing.Optional[openapi_models.SecurityScheme]

    def __init__(
        self,
        *,
        scheme_name: typing.Optional[str] = None,
        model: typing.Union[SecurityBase, typing.Type[SecurityBase]],
        scopes: typing.Optional[typing.Sequence[str]],
    ) -> None:
        self.model = model
        self.scopes = frozenset(scopes or [])
        if isinstance(model, SecurityBase):

            self._model = model.model
            self._scheme_name = scheme_name or model.__class__.__name__

            def get_model() -> SecurityBase:
                assert isinstance(model, SecurityBase)
                return model

            extractor = model.__class__.__call__
            self._model_dependant = Dependant(get_model, scope="app")
            super().__init__(
                call=extractor,
                overrides={"self": self._model_dependant},
                scope="connection",
            )
        else:
            self._model = None
            self._scheme_name = scheme_name or model.__name__
            self._model_dependant = Dependant(model, scope="app")
            super().__init__(
                call=model.__call__,
                overrides={"self": self._model_dependant},
                scope="connection",
            )

    @property
    def scheme_name(self) -> str:
        return self._scheme_name

    def construct_model(
        self, container: BaseContainer
    ) -> openapi_models.SecurityScheme:
        if self._model is not None:
            return self._model
        if "app" not in container.current_scopes:
            raise XpressoError(
                "Defered security models require a lifespan event to be triggered to be able to generate OpenAPI schemas"
                "\nIf you are using TestClient, use it as a context manager:"
                "\n  with TestClient(app) as client:  ..."
            )
        solved = container.solve(self._model_dependant)
        model = container.execute_sync(solved, executor=SyncExecutor())
        return model.model

    def register_parameter(self, param: inspect.Parameter) -> DependantBase[typing.Any]:
        return self

    @property
    def cache_key(self) -> CacheKey:
        return (self.__class__, self.model)
