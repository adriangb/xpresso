import typing

from di.api.dependencies import DependantBase
from di.api.executor import SupportsAsyncExecutor
from di.api.solved import SolvedDependant
from di.container import Container
from di.dependant import JoinedDependant
from di.executors import AsyncExecutor, ConcurrentAsyncExecutor
from starlette.datastructures import URLPath
from starlette.requests import HTTPConnection, Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, NoMatchFound, get_name
from starlette.types import ASGIApp, Receive, Scope, Send

import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso._utils.asgi import XpressoHTTPExtension
from xpresso._utils.endpoint_dependant import Endpoint, EndpointDependant
from xpresso.dependencies.models import Depends, Scopes
from xpresso.encoders.api import Encoder
from xpresso.encoders.json import JsonableEncoder
from xpresso.responses import Responses


class _OperationApp:
    __slots__ = (
        "container",
        "dependant",
        "executor",
        "response_factory",
        "response_encoder",
    )

    def __init__(
        self,
        dependant: SolvedDependant[typing.Any],
        container: Container,
        executor: SupportsAsyncExecutor,
        response_factory: typing.Callable[[typing.Any], Response],
        response_encoder: Encoder,
    ) -> None:
        self.container = container
        self.dependant = dependant
        self.executor = executor
        self.response_factory = response_factory
        self.response_encoder = response_encoder

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        xpresso_scope: XpressoHTTPExtension = scope["extensions"]["xpresso"]
        if xpresso_scope.request is None:
            request = Request(scope=scope, receive=receive, send=send)
            xpresso_scope.request = request
        else:
            request = xpresso_scope.request
        values: typing.Dict[typing.Any, typing.Any] = {
            Request: request,
            HTTPConnection: request,
        }
        async with xpresso_scope.di_container_state.enter_scope(
            "connection"
        ) as cpnn_state:
            async with cpnn_state.enter_scope("endpoint") as endpoint_state:
                endpoint_return = await self.container.execute_async(
                    self.dependant,
                    values=values,
                    executor=self.executor,
                    state=endpoint_state,
                )
                if isinstance(endpoint_return, Response):
                    response = endpoint_return
                else:
                    response = self.response_factory(
                        self.response_encoder(endpoint_return)
                    )
                xpresso_scope.response = response
            await response(scope, receive, send)
            xpresso_scope.response_sent = True


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
        responses: typing.Optional[Responses] = None,
        # xpresso params
        name: typing.Optional[str] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]]
        ] = None,
        execute_dependencies_concurrently: bool = False,
        response_factory: typing.Callable[[typing.Any], Response] = JSONResponse,
        response_encoder: Encoder = JsonableEncoder(),
        sync_to_thread: bool = True,
    ) -> None:
        self._app: typing.Optional[ASGIApp] = None
        self.endpoint = endpoint
        self.tags = tuple(tags or ())
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.servers = tuple(servers or ())
        self.external_docs = external_docs
        self.responses = dict(responses or {})
        self.dependencies = tuple(
            dep if not isinstance(dep, Depends) else dep.as_dependant()
            for dep in dependencies or ()
        )
        self.execute_dependencies_concurrently = execute_dependencies_concurrently
        self.response_factory = response_factory
        self.response_encoder = response_encoder
        self.include_in_schema = include_in_schema
        self.name: str = get_name(endpoint) if name is None else name  # type: ignore
        self.sync_to_thread = sync_to_thread

    async def handle(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if self._app is None:
            raise RuntimeError("Operation cannot be used outside of a Xpresso App")
        return await self._app(scope, receive, send)

    def solve(
        self,
        container: Container,
        dependencies: typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]],
    ) -> None:
        deps = [
            dep if not isinstance(dep, Depends) else dep.as_dependant()
            for dep in dependencies or ()
        ]
        self.dependant = container.solve(
            JoinedDependant(
                EndpointDependant(self.endpoint, sync_to_thread=self.sync_to_thread),
                siblings=[*deps, *self.dependencies],
            ),
            scopes=Scopes,
        )
        flat = self.dependant.get_flat_subdependants()
        bodies = [dep for dep in flat if isinstance(dep, param_dependants.BodyBinder)]
        if len(bodies) > 1:
            raise ValueError("There can only be 1 top level body per operation")
        executor: SupportsAsyncExecutor
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self._app = _OperationApp(
            container=container,
            dependant=self.dependant,
            executor=executor,
            response_encoder=self.response_encoder,
            response_factory=self.response_factory,
        )

    def url_path_for(self, name: str, **path_params: str) -> URLPath:
        if path_params:
            raise NoMatchFound(name, path_params)
        if name != self.name:
            raise NoMatchFound(name, path_params)
        return URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint
