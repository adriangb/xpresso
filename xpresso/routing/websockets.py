import typing

import starlette.requests
import starlette.responses
import starlette.routing
import starlette.types
import starlette.websockets
from di.api.dependencies import DependantBase
from di.api.executor import SupportsAsyncExecutor
from di.api.solved import SolvedDependant
from di.container import Container
from di.dependant import JoinedDependant
from di.executors import AsyncExecutor, ConcurrentAsyncExecutor

from xpresso._utils.asgi import XpressoWebSocketExtension
from xpresso._utils.endpoint_dependant import Endpoint, EndpointDependant
from xpresso.dependencies._dependencies import BoundDependsMarker, Scopes


class _WebSocketRoute:
    __slots__ = ("container", "dependant", "executor")

    def __init__(
        self,
        dependant: SolvedDependant[typing.Any],
        executor: SupportsAsyncExecutor,
        container: Container,
    ) -> None:
        self.dependant = dependant
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
                    self.dependant,
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
            typing.Iterable[typing.Union[DependantBase[typing.Any], BoundDependsMarker]]
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
            dep if isinstance(dep, DependantBase) else dep.as_dependant()
            for dep in dependencies or ()
        )
        self.execute_dependencies_concurrently = execute_dependencies_concurrently

    def prepare(
        self,
        container: Container,
        dependencies: typing.Iterable[DependantBase[typing.Any]],
    ) -> SolvedDependant[typing.Any]:
        self.dependant = container.solve(
            JoinedDependant(
                EndpointDependant(self.endpoint),
                siblings=[*dependencies, *self.dependencies],
            ),
            scopes=Scopes,
        )
        executor: SupportsAsyncExecutor
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self.app = _WebSocketRoute(
            dependant=self.dependant,
            executor=executor,
            container=container,
        )
        return self.dependant
