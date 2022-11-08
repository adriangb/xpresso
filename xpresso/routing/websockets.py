import typing

import starlette.requests
import starlette.responses
import starlette.routing
import starlette.types
import starlette.websockets
from di.api.dependencies import DependentBase
from di.api.executor import SupportsAsyncExecutor
from di.api.solved import SolvedDependent
from di.container import Container
from di.dependent import JoinedDependent
from di.executors import AsyncExecutor, ConcurrentAsyncExecutor

from xpresso._utils.asgi import XpressoWebSocketExtension
from xpresso._utils.endpoint_dependent import Endpoint, EndpointDependent
from xpresso._utils.scope_resolver import endpoint_scope_resolver
from xpresso.dependencies._dependencies import BoundDependsMarker, Scopes


class _WebSocketRoute:
    __slots__ = ("container", "dependent", "executor")

    def __init__(
        self,
        dependent: SolvedDependent[typing.Any],
        executor: SupportsAsyncExecutor,
        container: Container,
    ) -> None:
        self.dependent = dependent
        self.executor = executor
        self.container = container

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        xpresso_scope: XpressoWebSocketExtension = scope["extensions"]["xpresso"]
        ws = starlette.websockets.WebSocket(scope=scope, receive=receive, send=send)
        values: typing.Dict[typing.Any, typing.Any] = {
            starlette.websockets.WebSocket: ws,
            starlette.requests.HTTPConnection: ws,
        }
        async with self.container.enter_scope(
            "connection",
            state=xpresso_scope.di_container_state,
        ) as conn_state:
            async with self.container.enter_scope(
                "endpoint", state=conn_state
            ) as endpoint_state:
                await self.container.execute_async(
                    self.dependent,
                    values=values,
                    executor=self.executor,
                    state=endpoint_state,
                )


class WebSocketRoute(starlette.routing.WebSocketRoute):
    path: str

    def __init__(
        self,
        path: str,
        endpoint: Endpoint,
        *,
        name: typing.Optional[str] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependentBase[typing.Any], BoundDependsMarker]]
        ] = None,
        execute_dependencies_concurrently: bool = False,
    ) -> None:
        super().__init__(  # type: ignore
            path=path,
            endpoint=endpoint,
            name=name,  # type: ignore[arg-type]
        )
        self.endpoint = endpoint
        self.dependencies = tuple(
            dep if isinstance(dep, DependentBase) else dep.as_dependent()
            for dep in dependencies or ()
        )
        self.execute_dependencies_concurrently = execute_dependencies_concurrently

    def prepare(
        self,
        container: Container,
        dependencies: typing.Iterable[DependentBase[typing.Any]],
    ) -> SolvedDependent[typing.Any]:
        self.dependent = container.solve(
            JoinedDependent(
                EndpointDependent(self.endpoint),
                siblings=[*dependencies, *self.dependencies],
            ),
            scopes=Scopes,
            scope_resolver=endpoint_scope_resolver,
        )
        executor: SupportsAsyncExecutor
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self.app = _WebSocketRoute(
            dependent=self.dependent,
            executor=executor,
            container=container,
        )
        return self.dependent
