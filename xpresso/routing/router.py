import typing

import starlette.middleware
import starlette.routing
import starlette.types
from starlette.datastructures import URL, URLPath
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.routing import Match, NoMatchFound
from starlette.websockets import WebSocketClose

from xpresso.dependencies.models import Dependant
from xpresso.responses import Responses


class Router:
    __slots__ = (
        "routes",
        "_app",
        "dependencies",
        "tags",
        "responses",
        "_redirect_slashes",
        "_default",
    )

    routes: typing.Sequence[starlette.routing.BaseRoute]
    _app: starlette.types.ASGIApp

    def __init__(
        self,
        routes: typing.Sequence[starlette.routing.BaseRoute],
        *,
        redirect_slashes: bool = True,
        default: typing.Optional[starlette.types.ASGIApp] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        tags: typing.Optional[typing.List[str]] = None,
        responses: typing.Optional[Responses] = None,
        middleware: typing.Optional[
            typing.Sequence[starlette.middleware.Middleware]
        ] = None,
    ) -> None:
        self.dependencies = list(dependencies or [])
        self.tags = list(tags or [])
        self.responses = dict(responses or {})
        self._redirect_slashes = redirect_slashes
        self._default = self._not_found if default is None else default
        self.routes = tuple(routes)

        self._app = self._find_route  # type: ignore[assignment,misc]
        if middleware is not None:
            for cls, options in reversed(middleware):  # type: ignore
                self._app = cls(app=self._app, **options)  # type: ignore[assignment,misc]

    def __eq__(self, other: typing.Any) -> bool:
        return isinstance(other, Router) and self.routes == other.routes

    async def _not_found(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        if scope["type"] == "websocket":
            websocket_close = WebSocketClose()
            await websocket_close(scope, receive, send)
            return

        # If we're running inside a starlette application then raise an
        # exception, so that the configurable exception handler can deal with
        # returning the response. For plain ASGI apps, just return the response.
        if "app" in scope:
            raise HTTPException(status_code=404)
        else:
            response = PlainTextResponse("Not Found", status_code=404)
        await response(scope, receive, send)

    def url_path_for(self, name: str, **path_params: typing.Any) -> URLPath:
        for route in self.routes:
            try:
                return route.url_path_for(name, **path_params)
            except NoMatchFound:
                pass
        raise NoMatchFound()

    def _find_route(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> typing.Awaitable[None]:
        partial = None

        for route in self.routes:
            # Determine if any route matches the incoming scope,
            # and hand over to the matching route if found.
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                scope.update(child_scope)
                return route.handle(scope, receive, send)
            elif match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = child_scope

        if partial is not None:
            #  Handle partial matches. These are cases where an endpoint is
            # able to handle the request, but is not a preferred option.
            # We use this in particular to deal with "405 Method Not Allowed".
            scope.update(partial_scope)  # type: ignore  # partial_scope is always bound if partial is not None
            return partial.handle(scope, receive, send)

        if scope["type"] == "http" and self._redirect_slashes and scope["path"] != "/":
            redirect_scope = dict(scope)
            if scope["path"].endswith("/"):
                redirect_scope["path"] = redirect_scope["path"].rstrip("/")
            else:
                redirect_scope["path"] = redirect_scope["path"] + "/"

            for route in self.routes:
                match, child_scope = route.matches(redirect_scope)
                if match != Match.NONE:
                    redirect_url = URL(scope=redirect_scope)
                    response = RedirectResponse(url=str(redirect_url))
                    return response(scope, receive, send)

        return self._default(scope, receive, send)

    def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> typing.Awaitable[None]:

        if "router" not in scope:
            scope["router"] = self

        return self._app(scope, receive, send)  # type: ignore
