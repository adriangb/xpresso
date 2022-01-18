import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import starlette.applications
import starlette.background
import starlette.datastructures
import starlette.exceptions
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
from starlette.routing import Host as Host  # noqa: F401
from starlette.routing import Mount as Mount  # noqa: F401

import xpresso._utils.asgi_scope_extension as asgi_scope_extension
import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso.dependencies.models import Dependant
from xpresso.encoders.api import Encoder
from xpresso.encoders.json import JsonableEncoder
from xpresso.exceptions import HTTPException
from xpresso.responses import ResponseSpec

__all__ = (
    "APIRouter",
    "Operation",
    "Path",
    "Mount",
    "Host",
)

Method = Literal[
    "GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "CONNECT", "OPTIONS", "TACE"
]


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
        request = starlette.requests.Request(scope=scope, receive=receive, send=send)
        values: typing.Dict[typing.Any, typing.Any] = {
            starlette.requests.Request: request,
            starlette.requests.HTTPConnection: request,
            starlette.background.BackgroundTasks: starlette.background.BackgroundTasks(),
        }
        xpresso_scope: asgi_scope_extension.xpressoASGIExtension = scope["extensions"][
            "xpresso"
        ]
        async with xpresso_scope["container"].enter_scope("endpoint") as container:
            endpoint_return = await container.execute_async(
                self.dependant,
                values=values,
                executor=self.executor,
            )
            if isinstance(endpoint_return, starlette.responses.Response):
                response = endpoint_return
            else:
                response = self.response_factory(
                    self.response_encoder.encode(endpoint_return)
                )
            xpresso_scope["response"] = response
        await xpresso_scope["response"](scope, receive, send)


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

    async def handle(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        if self._app is None:
            raise RuntimeError("Operation cannot be used outside of a xpresso router")
        return await self._app(scope, receive, send)

    def solve(
        self,
        container: BaseContainer,
        path_params: typing.Set[str],
        dependencies: typing.List[DependantBase[typing.Any]],
    ) -> None:
        self.dependant = container.solve(
            JoinedDependant(
                Dependant(self.endpoint),
                siblings=[*dependencies, *(self.dependencies or ())],
            )
        )
        flat = self.dependant.get_flat_subdependants()
        bodies = [dep for dep in flat if isinstance(dep, param_dependants.BodyBinder)]
        if len(bodies) > 1:
            raise TypeError("There can only be 1 top level body per operation")
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
            raise TypeError("Operations cannot have path parameters")
        if name != self.name:
            raise starlette.routing.NoMatchFound()
        return starlette.datastructures.URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint


class _PathApp:
    """Thin class wrapper so that Starlette treats us as an ASGI App"""

    __slots__ = ("operations",)

    def __init__(self, operations: typing.Dict[str, Operation]) -> None:
        self.operations = operations

    def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> typing.Awaitable[None]:
        if scope["method"] not in self.operations:
            raise HTTPException(status_code=405, detail="Method not allowed")
        return self.operations[scope["method"]].handle(scope, receive, send)


class Path(starlette.routing.Route):
    def __init__(
        self,
        path: str,
        *,
        get: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        head: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        post: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        put: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        patch: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        delete: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        connect: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        options: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        trace: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        redirect_slashes: bool = True,
        dependencies: typing.Optional[typing.Sequence[Dependant]] = None,
        # OpenAPI metadata
        include_in_schema: bool = True,
        name: typing.Optional[str] = None,
        summary: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        servers: typing.Optional[typing.Sequence[openapi_models.Server]] = None,
        parameters: typing.Optional[
            typing.Sequence[param_dependants.ParameterBinderMarker]
        ] = None,
    ) -> None:
        if not path.startswith("/"):
            raise ValueError("Routed paths must start with '/'")
        self.path = path
        self.redirect_slashes = redirect_slashes
        self.dependencies = dependencies or []
        self.summary = summary
        self.description = description
        self.servers = servers
        self.parameters = parameters

        operations: typing.Dict[str, Operation] = {}
        if get:
            operations["GET"] = get if isinstance(get, Operation) else Operation(get)
        if head:
            operations["HEAD"] = (
                head if isinstance(head, Operation) else Operation(head)
            )
        if post:
            operations["POST"] = (
                post if isinstance(post, Operation) else Operation(post)
            )
        if put:
            operations["PUT"] = put if isinstance(put, Operation) else Operation(put)
        if patch:
            operations["PATCH"] = (
                patch if isinstance(patch, Operation) else Operation(patch)
            )
        if delete:
            operations["DELETE"] = (
                delete if isinstance(delete, Operation) else Operation(delete)
            )
        if connect:
            operations["CONNECT"] = (
                connect if isinstance(connect, Operation) else Operation(connect)
            )
        if options:
            operations["OPTIONS"] = (
                options if isinstance(options, Operation) else Operation(options)
            )
        if trace:
            operations["TRACE"] = (
                trace if isinstance(trace, Operation) else Operation(trace)
            )
        self.operations = operations
        super().__init__(  # type: ignore  # for Pylance
            path=path,
            endpoint=_PathApp(operations),
            name=name,  # type: ignore[arg-type]
            include_in_schema=include_in_schema,
            methods=list(operations.keys()),
        )


def _not_supported(method: str) -> typing.Callable[..., typing.Any]:
    def raise_error(*args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        raise NotImplementedError(
            f"Use of APIRouter.{method} is deprecated."
            " Use APIRouter(routes=[...]) instead."
        )

    return raise_error


class APIRouter(starlette.routing.Router):
    routes: typing.List[starlette.routing.BaseRoute]

    def __init__(
        self,
        routes: typing.Sequence[starlette.routing.BaseRoute],
        *,
        redirect_slashes: bool = True,
        default: typing.Optional[starlette.types.ASGIApp] = None,
        lifespan: typing.Optional[
            typing.Callable[
                [starlette.applications.Starlette], typing.AsyncContextManager[None]
            ]
        ] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
    ) -> None:
        self.dependencies = dependencies or []
        super().__init__(  # type: ignore
            routes=list(routes),
            redirect_slashes=redirect_slashes,
            default=default,  # type: ignore
            lifespan=lifespan,  # type: ignore
        )

    mount = _not_supported("mount")
    host = _not_supported("host")
    add_route = _not_supported("add_route")
    add_websocket_route = _not_supported("add_websocket_route")
    route = _not_supported("route")
    websocket_route = _not_supported("websocket_route")
    add_event_handler = _not_supported("add_event_handler")
    on_event = _not_supported("on_event")
