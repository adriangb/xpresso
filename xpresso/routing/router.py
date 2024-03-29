import typing

import starlette.middleware
from di.api.dependencies import DependentBase
from starlette.routing import BaseRoute
from starlette.routing import Router as StarletteRouter
from starlette.types import Receive, Scope, Send

from xpresso._utils.typing import Protocol
from xpresso.dependencies._dependencies import BoundDependsMarker
from xpresso.responses import ResponseSpec, ResponseStatusCode


class _ASGIApp(Protocol):
    def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> typing.Awaitable[None]:
        ...


_MiddlewareIterator = typing.Iterable[
    typing.Tuple[typing.Callable[..., _ASGIApp], typing.Mapping[str, typing.Any]]
]


class Router:
    routes: typing.Sequence[BaseRoute]
    lifespan: typing.Optional[typing.Callable[..., typing.AsyncContextManager[None]]]
    dependencies: typing.Sequence[DependentBase[typing.Any]]
    tags: typing.Sequence[str]
    include_in_schema: bool
    _app: _ASGIApp

    __slots__ = (
        "_app",
        "_router",
        "dependencies",
        "include_in_schema",
        "lifespan",
        "responses",
        "routes",
        "tags",
    )

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
        default: typing.Optional[_ASGIApp] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependentBase[typing.Any], BoundDependsMarker]]
        ] = None,
        tags: typing.Optional[typing.List[str]] = None,
        responses: typing.Optional[
            typing.Mapping[ResponseStatusCode, ResponseSpec]
        ] = None,
        include_in_schema: bool = True,
    ) -> None:
        self.routes = list(routes)
        self.lifespan = lifespan
        self._router = StarletteRouter(
            routes=self.routes,
            redirect_slashes=redirect_slashes,
            default=default,  # type: ignore[arg-type]
            lifespan=lifespan,  # type: ignore[arg-type]
        )
        self.dependencies = tuple(
            dep if isinstance(dep, DependentBase) else dep.as_dependent()
            for dep in dependencies or ()
        )
        self.tags = list(tags or [])
        self.responses = dict(responses or {})
        self.include_in_schema = include_in_schema
        self._app = self._router.__call__
        if middleware is not None:
            for cls, options in typing.cast(_MiddlewareIterator, reversed(middleware)):
                self._app = cls(app=self._app, **options)

    def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> typing.Awaitable[None]:
        return self._app(scope, receive, send)
