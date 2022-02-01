import typing

from di import AsyncExecutor, BaseContainer, ConcurrentAsyncExecutor
from di.api.dependencies import DependantBase
from di.api.executor import AsyncExecutorProtocol
from di.api.providers import DependencyProvider as Endpoint
from di.api.solved import SolvedDependant
from di.dependant import JoinedDependant
from starlette.datastructures import URLPath
from starlette.requests import HTTPConnection, Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, NoMatchFound, get_name
from starlette.types import ASGIApp, Receive, Scope, Send

import xpresso._utils.asgi_scope_extension as asgi_scope_extension
import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso.dependencies.models import Dependant
from xpresso.encoders.api import Encoder
from xpresso.encoders.json import JsonableEncoder
from xpresso.responses import Responses


class _OperationApp:
    __slots__ = ("dependant", "executor", "response_factory", "response_encoder")

    def __init__(
        self,
        dependant: SolvedDependant[typing.Any],
        executor: AsyncExecutorProtocol,
        response_factory: typing.Callable[[typing.Any], Response],
        response_encoder: Encoder,
    ) -> None:
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
        request = Request(scope=scope, receive=receive, send=send)
        values: typing.Dict[typing.Any, typing.Any] = {
            Request: request,
            HTTPConnection: request,
        }
        xpresso_scope: asgi_scope_extension.XpressoASGIExtension = scope["extensions"][
            "xpresso"
        ]
        async with xpresso_scope["container"].enter_scope("endpoint") as container:
            endpoint_return = await container.execute_async(
                self.dependant,
                values=values,
                executor=self.executor,
            )
            if isinstance(endpoint_return, Response):
                response = endpoint_return
            else:
                response = self.response_factory(self.response_encoder(endpoint_return))
            xpresso_scope["response"] = response
        await response(scope, receive, send)


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
        dependencies: typing.Optional[typing.Sequence[Dependant]] = None,
        execute_dependencies_concurrently: bool = False,
        response_factory: typing.Callable[[typing.Any], Response] = JSONResponse,
        response_encoder: Encoder = JsonableEncoder(),
        sync_to_thread: bool = True,
    ) -> None:
        self._app: typing.Optional[ASGIApp] = None
        self.endpoint = endpoint
        self.tags = list(tags or [])
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.servers = list(servers or [])
        self.external_docs = external_docs
        self.responses = dict(responses or {})
        self.dependencies = list(dependencies or [])
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
        container: BaseContainer,
        dependencies: typing.List[DependantBase[typing.Any]],
    ) -> None:
        self.dependant = container.solve(
            JoinedDependant(
                Dependant(
                    self.endpoint, scope="endpoint", sync_to_thread=self.sync_to_thread
                ),
                siblings=[*dependencies, *(self.dependencies or ())],
            )
        )
        flat = self.dependant.get_flat_subdependants()
        bodies = [dep for dep in flat if isinstance(dep, param_dependants.BodyBinder)]
        if len(bodies) > 1:
            raise ValueError("There can only be 1 top level body per operation")
        executor: AsyncExecutorProtocol
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self._app = _OperationApp(
            dependant=self.dependant,
            executor=executor,
            response_encoder=self.response_encoder,
            response_factory=self.response_factory,
        )

    def url_path_for(self, name: str, **path_params: str) -> URLPath:
        if path_params:
            raise NoMatchFound()
        if name != self.name:
            raise NoMatchFound()
        return URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint
