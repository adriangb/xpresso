import typing

import starlette.requests
import starlette.responses
import starlette.routing
import starlette.types
import starlette.websockets
from di import AsyncExecutor, BaseContainer, ConcurrentAsyncExecutor, JoinedDependant
from di.api.dependencies import DependantBase
from di.api.executor import AsyncExecutorProtocol
from di.api.solved import SolvedDependant

from xpresso._utils.asgi import XpressoWebSocketExtension
from xpresso._utils.endpoint_dependant import Endpoint, EndpointDependant


class _WebSocketRoute:
    __slots__ = ("dependant", "executor")

    def __init__(
        self,
        dependant: SolvedDependant[typing.Any],
        executor: AsyncExecutorProtocol,
    ) -> None:
        self.dependant = dependant
        self.executor = executor

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        xpresso_scope: XpressoWebSocketExtension = scope["extensions"]["xpresso"]
        if xpresso_scope.websocket is None:
            ws = starlette.websockets.WebSocket(scope=scope, receive=receive, send=send)
            xpresso_scope.websocket = ws
        else:
            ws = xpresso_scope.websocket
        values: typing.Dict[typing.Any, typing.Any] = {
            starlette.websockets.WebSocket: ws,
            starlette.requests.HTTPConnection: ws,
        }
        async with xpresso_scope.container.enter_scope("connection") as container:
            async with container.enter_scope("endpoint") as container:
                await container.execute_async(
                    self.dependant,
                    values=values,
                    executor=self.executor,
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
            typing.Sequence[DependantBase[typing.Any]]
        ] = None,
        execute_dependencies_concurrently: bool = False,
    ) -> None:
        super().__init__(  # type: ignore
            path=path,
            endpoint=endpoint,
            name=name,  # type: ignore[arg-type]
        )
        self.endpoint = endpoint
        self.dependencies = dependencies or []
        self.execute_dependencies_concurrently = execute_dependencies_concurrently

    def solve(
        self,
        container: BaseContainer,
        dependencies: typing.List[DependantBase[typing.Any]],
    ) -> None:
        self.dependant = container.solve(
            JoinedDependant(
                EndpointDependant(self.endpoint),
                siblings=[*dependencies, *(self.dependencies or ())],
            )
        )
        executor: AsyncExecutorProtocol
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self.app = _WebSocketRoute(
            dependant=self.dependant,
            executor=executor,
        )
