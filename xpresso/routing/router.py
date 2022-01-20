import typing

import starlette.applications
import starlette.background
import starlette.datastructures
import starlette.exceptions
import starlette.requests
import starlette.responses
import starlette.routing
import starlette.status
import starlette.types

from xpresso.dependencies.models import Dependant


def _not_supported(method: str) -> typing.Callable[..., typing.Any]:
    def raise_error(*args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        raise NotImplementedError(
            f"Use of Router.{method} is deprecated."
            " Use Router(routes=[...]) instead."
        )

    return raise_error


class Router(starlette.routing.Router):
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
