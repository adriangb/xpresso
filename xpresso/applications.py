import traceback
import typing
from contextlib import asynccontextmanager

import starlette.types
from di import AsyncExecutor, BaseContainer
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProviderType
from starlette.datastructures import State
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.routing import Route as StarletteRoute

from xpresso._utils.asgi_scope_extension import XpressoASGIExtension
from xpresso._utils.routing import visit_routes
from xpresso.dependencies.models import Dependant
from xpresso.dependencies.utils import register_framework_dependencies
from xpresso.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from xpresso.exceptions import HTTPException, RequestValidationError
from xpresso.middleware.exceptions import ExceptionMiddleware
from xpresso.openapi import models as openapi_models
from xpresso.openapi._builder import SecurityModels, genrate_openapi
from xpresso.openapi._html import get_swagger_ui_html
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router
from xpresso.routing.websockets import WebSocketRoute
from xpresso.security._dependants import Security

ExceptionHandler = typing.Callable[
    [Request, Exception], typing.Union[Response, typing.Awaitable[Response]]
]
ExceptionHandlers = typing.Mapping[
    typing.Union[typing.Type[Exception], int], ExceptionHandler
]


def _include_error_middleware(
    debug: bool,
    user_middleware: typing.Iterable[Middleware],
    exception_handlers: ExceptionHandlers,
) -> typing.Sequence[Middleware]:
    # user's exception handlers come last so that they can override
    # the default exception handlers
    exception_handlers = {
        RequestValidationError: validation_exception_handler,
        HTTPException: http_exception_handler,
        **exception_handlers,
    }

    error_handler = None
    for key, value in exception_handlers.items():
        if key in (500, Exception):
            error_handler = value
        else:
            exception_handlers[key] = value

    return (
        Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug),
        *user_middleware,
        Middleware(ExceptionMiddleware, handlers=exception_handlers, debug=debug),
    )


class App:
    __slots__ = (
        "router",
        "openapi",
        "state",
        "container",
        "openapi_version",
        "openapi_info",
        "servers",
        "_lifespan_ctx",
        "_debug",
        "_setup_run",
    )

    router: Router
    openapi: typing.Optional[openapi_models.OpenAPI]
    state: State
    container: BaseContainer

    def __init__(
        self,
        routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
        *,
        container: typing.Optional[BaseContainer] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        debug: bool = False,
        middleware: typing.Optional[typing.Sequence[Middleware]] = None,
        exception_handlers: typing.Optional[ExceptionHandlers] = None,
        lifespan: typing.Optional[DependencyProviderType[None]] = None,
        openapi_version: str = "3.0.3",
        title: str = "API",
        description: typing.Optional[str] = None,
        version: str = "0.1.0",
        openapi_url: typing.Optional[str] = "/openapi.json",
        docs_url: typing.Optional[str] = "/docs",
        servers: typing.Optional[typing.Iterable[openapi_models.Server]] = None,
    ) -> None:
        self.container = container or BaseContainer(
            scopes=("app", "connection", "operation")
        )
        register_framework_dependencies(self.container)
        self._setup_run = False

        @asynccontextmanager
        async def lifespan_ctx() -> typing.AsyncGenerator[None, None]:
            self._setup()
            self._setup_run = True
            original_container = self.container
            async with self.container.enter_scope("app") as container:
                self.container = container
                if lifespan is not None:
                    await container.execute_async(
                        self.container.solve(Dependant(call=lifespan, scope="app")),
                        executor=AsyncExecutor(),
                    )
                try:
                    yield
                finally:
                    # make this cm reentrant for testing purposes
                    self.container = original_container
                    self._setup_run = False

        self._lifespan_ctx = lifespan_ctx

        self._debug = debug
        self.state = State()

        routes = list(routes or [])
        routes.extend(
            self._get_doc_routes(
                openapi_url=openapi_url,
                docs_url=docs_url,
            )
        )
        middleware = _include_error_middleware(
            debug=debug,
            user_middleware=middleware or (),
            exception_handlers=exception_handlers or {},
        )
        self.router = Router(routes, dependencies=dependencies, middleware=middleware)

        self.openapi_version = openapi_version
        self.openapi_info = openapi_models.Info(
            title=title,
            version=version,
            description=description,
        )
        self.servers = servers
        self.openapi = None

    async def _lifespan(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        started = False
        await receive()
        try:
            async with self._lifespan_ctx():
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()
        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
        else:
            await send({"type": "lifespan.shutdown.complete"})

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        self._setup()
        scope["app"] = self
        scope_type = scope["type"]
        if scope_type == "http" or scope_type == "websocket":
            extensions = scope.get("extensions", None) or {}
            scope["extensions"] = extensions
            xpresso_scope = extensions.get("xpresso", None)
            if xpresso_scope is None:
                async with self.container.enter_scope("connection") as container:
                    xpresso_asgi_extension: XpressoASGIExtension = {
                        "container": container,
                        "response_sent": False,
                    }
                    extensions["xpresso"] = xpresso_asgi_extension
                    await self.router(scope, receive, send)
                    xpresso_asgi_extension["response_sent"] = True
                    return
        elif scope_type == "lifespan":
            await self._lifespan(scope, receive, send)
            return
        await self.router(scope, receive, send)

    def _setup(self) -> None:
        if self._setup_run:
            return
        for route in visit_routes([self.router]):
            dependencies: typing.List[DependantBase[typing.Any]] = []
            for router in route.routers:
                if isinstance(router, Router):
                    dependencies.extend(router.dependencies)
            if isinstance(route.route, Path):
                for operation in route.route.operations.values():
                    operation.solve(
                        dependencies=[
                            *dependencies,
                            *route.route.dependencies,
                            *operation.dependencies,
                        ],
                        container=self.container,
                    )
            if isinstance(route.route, WebSocketRoute):
                route.route.solve(
                    dependencies=[
                        *dependencies,
                        *route.route.dependencies,
                    ],
                    container=self.container,
                )

    async def get_openapi(self) -> openapi_models.OpenAPI:
        return genrate_openapi(
            version=self.openapi_version,
            info=self.openapi_info,
            servers=self.servers,
            router=self.router,
            security_models=await self.gather_security_models(),
        )

    async def gather_security_models(self) -> SecurityModels:
        security_dependants: typing.List[Security] = []
        for route in visit_routes([self.router]):
            if isinstance(route.route, Path):
                for operation in route.route.operations.values():
                    dependant = operation.dependant
                    assert dependant is not None
                    for subdependant in dependant.dag:
                        if isinstance(subdependant, Security):
                            security_dependants.append(subdependant)
        executor = AsyncExecutor()
        return {
            sec_dep: await self.container.execute_async(
                self.container.solve(sec_dep),
                executor=executor,
            )
            for sec_dep in security_dependants
        }

    def _get_doc_routes(
        self,
        openapi_url: typing.Optional[str],
        docs_url: typing.Optional[str],
    ) -> typing.Iterable[BaseRoute]:
        routes: typing.List[BaseRoute] = []

        if openapi_url:
            openapi_url = openapi_url

            async def openapi(req: Request) -> JSONResponse:
                if self.openapi is None:
                    self.openapi = await self.get_openapi()
                res = JSONResponse(self.openapi.dict(exclude_none=True, by_alias=True))
                return res

            routes.append(
                StarletteRoute(
                    path=openapi_url, endpoint=openapi, include_in_schema=False
                )
            )
        if openapi_url and docs_url:

            openapi_url = openapi_url

            async def swagger_ui_html(req: Request) -> HTMLResponse:
                root_path: str = req.scope.get("root_path", "").rstrip("/")  # type: ignore  # for Pylance
                full_openapi_url = root_path + openapi_url  # type: ignore[operator]
                return get_swagger_ui_html(
                    openapi_url=full_openapi_url,
                    title=self.openapi_info.title + " - Swagger UI",
                    oauth2_redirect_url=None,
                    init_oauth=None,
                )

            routes.append(
                StarletteRoute(
                    path=docs_url,
                    endpoint=swagger_ui_html,
                    include_in_schema=False,
                )
            )

        return routes
