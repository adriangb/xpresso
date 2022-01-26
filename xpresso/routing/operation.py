import typing

import starlette.applications
import starlette.background
import starlette.datastructures
import starlette.requests
import starlette.responses
import starlette.routing
import starlette.status
import starlette.types
from di import AsyncExecutor, BaseContainer, ConcurrentAsyncExecutor
from di.api.dependencies import DependantBase
from di.api.executor import AsyncExecutorProtocol
from di.api.providers import DependencyProvider as Endpoint
from di.api.solved import SolvedDependant
from di.dependant import JoinedDependant

import xpresso._utils.asgi_scope_extension as asgi_scope_extension
import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso.dependencies.models import Dependant
from xpresso.encoders.api import Encoder
from xpresso.encoders.json import JsonableEncoder
from xpresso.responses import ResponseSpec


class _OperationApp:
    __slots__ = ("dependant", "executor", "response_factory", "response_encoder")

    def __init__(
        self,
        dependant: SolvedDependant[typing.Any],
        executor: AsyncExecutorProtocol,
        response_factory: typing.Callable[[typing.Any], starlette.responses.Response],
        response_encoder: Encoder,
    ) -> None:
        self.dependant = dependant
        self.executor = executor
        self.response_factory = response_factory
        self.response_encoder = response_encoder

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        values: typing.Dict[typing.Any, typing.Any] = {
            starlette.requests.Request: starlette.requests.Request(
                scope=scope, receive=receive, send=send
            ),
            starlette.requests.HTTPConnection: starlette.requests.HTTPConnection(
                scope=scope, receive=receive
            ),
            starlette.background.BackgroundTasks: starlette.background.BackgroundTasks(),
            starlette.types.Scope: scope,
            starlette.types.Receive: receive,
            starlette.types.Send: send,
        }
        xpresso_scope: asgi_scope_extension.XpressoASGIExtension = scope["extensions"][
            "xpresso"
        ]
        async with xpresso_scope["container"].enter_scope("operation") as container:
            endpoint_return = await container.execute_async(
                self.dependant,
                values=values,
                executor=self.executor,
            )
            if isinstance(endpoint_return, starlette.responses.Response):
                response = endpoint_return
            else:
                response = self.response_factory(self.response_encoder(endpoint_return))
            xpresso_scope["response"] = response
        await response(scope, receive, send)


class Operation(starlette.routing.BaseRoute):
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
            typing.Mapping[
                typing.Union[int, str],
                typing.Union[ResponseSpec, typing.Iterable[ResponseSpec]],
            ]
        ] = None,
        # xpresso params
        name: typing.Optional[str] = None,
        dependencies: typing.Optional[typing.Sequence[Dependant]] = None,
        execute_dependencies_concurrently: bool = False,
        response_factory: typing.Callable[
            [typing.Any], starlette.responses.Response
        ] = starlette.responses.JSONResponse,
        response_encoder: Encoder = JsonableEncoder(),
        sync_to_thread: bool = True,
    ) -> None:
        self._app: typing.Optional[starlette.types.ASGIApp] = None
        self.endpoint = endpoint
        self.tags = tags
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.servers = servers
        self.external_docs = external_docs
        self.responses = dict(responses or {})
        self.dependencies = dependencies or []
        self.execute_dependencies_concurrently = execute_dependencies_concurrently
        self.response_factory = response_factory
        self.response_encoder = response_encoder
        self.include_in_schema = include_in_schema
        self.name: str = starlette.routing.get_name(endpoint) if name is None else name  # type: ignore
        self.sync_to_thread = sync_to_thread

    async def handle(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
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
                    self.endpoint, scope="operation", sync_to_thread=self.sync_to_thread
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

    def url_path_for(
        self, name: str, **path_params: str
    ) -> starlette.datastructures.URLPath:
        if path_params:
            raise starlette.routing.NoMatchFound()
        if name != self.name:
            raise starlette.routing.NoMatchFound()
        return starlette.datastructures.URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint
