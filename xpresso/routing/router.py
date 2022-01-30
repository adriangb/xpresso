import typing

from starlette.applications import Starlette
from starlette.routing import BaseRoute
from starlette.routing import Router as StarletteRouter
from starlette.types import ASGIApp

from xpresso.dependencies.models import Dependant
from xpresso.responses import Responses


def _not_supported(method: str) -> typing.Callable[..., typing.Any]:
    def raise_error(*args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        raise NotImplementedError(
            f"Use of Router.{method} is deprecated."
            " Use Router(routes=[...]) instead."
        )

    return raise_error


class Router(StarletteRouter):
    routes: typing.List[BaseRoute]

    def __init__(
        self,
        routes: typing.Sequence[BaseRoute],
        *,
        redirect_slashes: bool = True,
        default: typing.Optional[ASGIApp] = None,
        lifespan: typing.Optional[
            typing.Callable[[Starlette], typing.AsyncContextManager[None]]
        ] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        tags: typing.Optional[typing.List[str]] = None,
        responses: typing.Optional[Responses] = None,
    ) -> None:
        super().__init__(  # type: ignore
            routes=list(routes),
            redirect_slashes=redirect_slashes,
            default=default,  # type: ignore
            lifespan=lifespan,  # type: ignore
        )
        self.dependencies = list(dependencies or [])
        self.tags = list(tags or [])
        self.responses = dict(responses or {})

    mount = _not_supported("mount")
    host = _not_supported("host")
    add_route = _not_supported("add_route")
    add_websocket_route = _not_supported("add_websocket_route")
    route = _not_supported("route")
    websocket_route = _not_supported("websocket_route")
    add_event_handler = _not_supported("add_event_handler")
    on_event = _not_supported("on_event")
