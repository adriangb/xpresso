import typing
from functools import partial

from di.api.dependencies import DependantBase
from di.api.executor import SupportsAsyncExecutor
from di.api.solved import SolvedDependant
from di.container import Container
from di.dependant import JoinedDependant
from di.executors import AsyncExecutor, ConcurrentAsyncExecutor
from starlette.datastructures import URLPath
from starlette.requests import HTTPConnection, Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, NoMatchFound, get_name  # type: ignore
from starlette.types import ASGIApp, Receive, Scope, Send

import xpresso.openapi.models as openapi_models
from xpresso._utils.asgi import XpressoHTTPExtension
from xpresso._utils.endpoint_dependant import Endpoint, EndpointDependant
from xpresso.dependencies._dependencies import BoundDependsMarker, Scopes
from xpresso.encoders import Encoder, JsonableEncoder
from xpresso.responses import ResponseSpec, ResponseStatusCode, TypeUnset


class NotPreparedError(Exception):
    pass


class _OperationApp(typing.NamedTuple):
    dependant: SolvedDependant[typing.Any]
    container: Container
    executor: SupportsAsyncExecutor
    response_factory: typing.Callable[[typing.Any], Response]
    response_encoder: typing.Optional[Encoder]

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        xpresso_scope: "XpressoHTTPExtension" = scope["extensions"]["xpresso"]
        request = Request(scope=scope, receive=receive, send=send)
        values: "typing.Dict[typing.Any, typing.Any]" = {
            Request: request,
            HTTPConnection: request,
        }
        async with self.container.enter_scope(
            "connection",
            xpresso_scope.di_container_state,
        ) as connection_state:
            async with connection_state.enter_scope("endpoint") as endpoint_state:
                endpoint_return = await self.container.execute_async(
                    self.dependant,
                    values=values,
                    executor=self.executor,
                    state=endpoint_state,
                )
                if isinstance(endpoint_return, Response):
                    response = endpoint_return
                else:
                    if self.response_encoder:
                        endpoint_return = self.response_encoder(endpoint_return)
                    response = self.response_factory(endpoint_return)
                xpresso_scope.response = response
            await response(scope, receive, send)
            xpresso_scope.response_sent = True


async def _not_prepared_app(*args: typing.Any) -> None:
    raise NotPreparedError(
        "Operation.prepare() was never called on this Operation."
        " Perhaps you tried to use an Xpresso Operation outside of an Xpresso App?"
    )


class Operation(BaseRoute):
    def __init__(
        self,
        endpoint: Endpoint,
        *,
        # OpenAPI parameters
        include_in_schema: bool = True,
        tags: typing.Optional[typing.Sequence[str]] = None,
        summary: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        deprecated: typing.Optional[bool] = None,
        operation_id: typing.Optional[bool] = None,
        servers: typing.Optional[typing.Sequence[openapi_models.Server]] = None,
        external_docs: typing.Optional[openapi_models.ExternalDocumentation] = None,
        responses: typing.Optional[
            typing.Mapping[ResponseStatusCode, ResponseSpec]
        ] = None,
        # xpresso params
        name: typing.Optional[str] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependantBase[typing.Any], BoundDependsMarker]]
        ] = None,
        execute_dependencies_concurrently: bool = False,
        response_factory: typing.Optional[
            typing.Callable[[typing.Any], Response]
        ] = None,
        response_encoder: typing.Optional[Encoder] = JsonableEncoder(),
        sync_to_thread: bool = True,
        # responses
        response_status_code: int = 200,
        response_media_type: str = "application/json",
        response_model: typing.Any = TypeUnset,
        response_description: typing.Optional[str] = None,
        response_examples: typing.Optional[
            typing.Mapping[str, typing.Union[openapi_models.Example, typing.Any]]
        ] = None,
        response_headers: typing.Optional[
            typing.Mapping[str, typing.Union[openapi_models.ResponseHeader, str]]
        ] = None,
    ) -> None:
        # These fields mirror Starlette's Route
        self.endpoint = endpoint
        self.include_in_schema = include_in_schema
        self.name: str = get_name(endpoint) if name is None else name  # type: ignore
        self.tags = tuple(tags or ())
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.servers = tuple(servers or ())
        self.external_docs = external_docs
        self.responses = dict(responses or {})
        self.response_status_code = response_status_code
        self.response_media_type = response_media_type
        self.response_model = response_model
        self.response_description = response_description
        self.response_examples = response_examples
        self.response_headers = response_headers
        self.dependencies = tuple(
            dep if isinstance(dep, DependantBase) else dep.as_dependant()
            for dep in dependencies or ()
        )
        self._app: ASGIApp = _not_prepared_app
        self._execute_dependencies_concurrently = execute_dependencies_concurrently
        self._response_factory = response_factory or partial(
            JSONResponse,
            media_type=response_media_type,
            status_code=response_status_code,
        )
        self._response_encoder = response_encoder
        self._sync_to_thread = sync_to_thread

    async def handle(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        return await self._app(scope, receive, send)

    def prepare(
        self,
        container: Container,
        dependencies: typing.Iterable[DependantBase[typing.Any]],
    ) -> SolvedDependant[typing.Any]:
        self.dependant = container.solve(
            JoinedDependant(
                EndpointDependant(self.endpoint, sync_to_thread=self._sync_to_thread),
                siblings=[*dependencies, *self.dependencies],
            ),
            scopes=Scopes,
        )
        executor: SupportsAsyncExecutor
        if self._execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self._app = _OperationApp(  # type: ignore[assignment]
            container=container,
            dependant=self.dependant,
            executor=executor,
            response_encoder=self._response_encoder,
            response_factory=self._response_factory,
        )
        return self.dependant

    def url_path_for(self, name: str, **path_params: str) -> URLPath:
        if path_params:
            raise NoMatchFound(name, path_params)
        if name != self.name:
            raise NoMatchFound(name, path_params)
        return URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint
