import typing

import starlette.middleware
from starlette.routing import BaseRoute
from starlette.routing import Router as StarletteRouter
from starlette.types import ASGIApp, Receive, Scope, Send

from xpresso._utils.deprecation import not_supported
from xpresso.dependencies.models import Dependant
from xpresso.responses import Responses


class Router(StarletteRouter):
    routes: typing.List[BaseRoute]
    _app: ASGIApp

    def __init__(
        self,
        routes: typing.Sequence[BaseRoute],
        *,
        middleware: typing.Optional[
            typing.Sequence[starlette.middleware.Middleware]
        ] = None,
        lifespan: typing.Optional[
            typing.Callable[..., typing.AsyncContextManager[None]]
        ] = None,
        redirect_slashes: bool = True,
        default: typing.Optional[ASGIApp] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        tags: typing.Optional[typing.List[str]] = None,
        responses: typing.Optional[Responses] = None,
        include_in_schema: bool = True,
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
        self.include_in_schema = include_in_schema
        self._app = super().__call__  # type: ignore[assignment,misc]
        if middleware is not None:
            for cls, options in reversed(middleware):  # type: ignore  # for Pylance
                self._app = cls(app=self._app, **options)  # type: ignore[assignment,misc]

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:

        if "router" not in scope:
            scope["router"] = self

        await self._app(scope, receive, send)  # type: ignore[arg-type,call-arg,misc]

    mount = not_supported("mount")
    host = not_supported("host")
    add_route = not_supported("add_route")
    add_websocket_route = not_supported("add_websocket_route")
    route = not_supported("route")
    websocket_route = not_supported("websocket_route")
    add_event_handler = not_supported("add_event_handler")
    on_event = not_supported("on_event")
