import typing

import starlette.requests
import starlette.responses
import starlette.routing
import starlette.types
import starlette.websockets
from di import AsyncExecutor, BaseContainer, ConcurrentAsyncExecutor
from di.api.dependencies import DependantBase
from di.api.executor import AsyncExecutorProtocol
from di.api.providers import DependencyProvider as Endpoint
from di.api.solved import SolvedDependant
from di.dependant import JoinedDependant

import xpresso._utils.asgi_scope_extension as asgi_scope_extension
from xpresso.dependencies.models import Dependant


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
        ws = starlette.websockets.WebSocket(scope=scope, receive=receive, send=send)
        values: typing.Dict[typing.Any, typing.Any] = {
            starlette.websockets.WebSocket: ws,
            starlette.requests.HTTPConnection: ws,
        }
        xpresso_scope: asgi_scope_extension.XpressoASGIExtension = scope["extensions"][
            "xpresso"
        ]
        async with xpresso_scope["container"].enter_scope("endpoint") as container:
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
        dependencies: typing.Optional[typing.Sequence[Dependant]] = None,
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
                Dependant(self.endpoint, scope="endpoint"),
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
