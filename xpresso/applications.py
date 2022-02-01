import inspect
import traceback
import typing

import starlette.types
from di import AsyncExecutor, BaseContainer, JoinedDependant
from di.api.dependencies import DependantBase
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


def _wrap_lifespan_as_async_generator(
    lifespan: typing.Callable[..., typing.AsyncContextManager[None]]
) -> typing.Callable[..., typing.AsyncIterator[None]]:
    async def gen(
        *args: typing.Any, **kwargs: typing.Any
    ) -> typing.AsyncIterator[None]:
        async with lifespan(*args, **kwargs):
            yield

    sig = inspect.signature(gen)
    sig = sig.replace(parameters=list(inspect.signature(lifespan).parameters.values()))
    setattr(gen, "__signature__", sig)

    return gen


class App:
    router: Router
    openapi: typing.Optional[openapi_models.OpenAPI]
    state: State
    container: BaseContainer
    _lifespans: typing.List[typing.Callable[..., typing.AsyncIterator[None]]]

    def __init__(
        self,
        routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
        *,
        container: typing.Optional[BaseContainer] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        debug: bool = False,
        middleware: typing.Optional[typing.Sequence[Middleware]] = None,
        exception_handlers: typing.Optional[ExceptionHandlers] = None,
        lifespan: typing.Optional[
            typing.Callable[..., typing.AsyncContextManager[None]]
        ] = None,
        include_in_schema: bool = True,
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

        self.lifespan = lifespan
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
        self.router = Router(
            routes,
            dependencies=dependencies,
            middleware=middleware,
            include_in_schema=include_in_schema,
        )

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
            self._setup()
            self._setup_run = True
            original_container = self.container
            async with self.container.enter_scope("app") as container:
                self.container = container

                def placeholder() -> None:
                    ...

                solved = self.container.solve(
                    JoinedDependant(
                        Dependant(placeholder, scope="app"),
                        siblings=[
                            Dependant(lifespan, scope="app")
                            for lifespan in self._lifespans
                        ],
                    )
                )
                await container.execute_async(solved, executor=AsyncExecutor())
                try:
                    await send({"type": "lifespan.startup.complete"})
                    started = True
                    await receive()
                finally:
                    # make this cm reentrant for testing purposes
                    self.container = original_container
                    self._setup_run = False
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
        scope["app"] = self
        scope_type = scope["type"]
        if scope_type == "http" or scope_type == "websocket":
            if not self._setup_run:
                self._setup()
            extensions = scope.get("extensions", None) or {}
            scope["extensions"] = extensions
            xpresso_asgi_extension: XpressoASGIExtension = extensions.get("xpresso", None) or {}  # type: ignore[assignment]
            extensions["xpresso"] = xpresso_asgi_extension
            async with self.container.enter_scope("connection") as container:
                xpresso_asgi_extension["response_sent"] = False
                xpresso_asgi_extension["container"] = container
                await self.router(scope, receive, send)
                xpresso_asgi_extension["response_sent"] = True
            return
        else:  # lifespan
            await self._lifespan(scope, receive, send)
            return

    def _setup(self) -> None:
        self._lifespans: typing.List[
            typing.Callable[..., typing.AsyncIterator[None]]
        ] = []
        for route in visit_routes(app_type=App, router=self.router, nodes=[self, self.router], path=""):  # type: ignore[misc]
            dependencies: typing.List[DependantBase[typing.Any]] = []
            for router_or_app in route.nodes:
                if isinstance(router_or_app, Router):
                    dependencies.extend(router_or_app.dependencies)
                elif isinstance(router_or_app, App):
                    lifespan = router_or_app.lifespan
                    if lifespan is not None:
                        self._lifespans.append(
                            _wrap_lifespan_as_async_generator(lifespan)
                        )
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
            elif isinstance(route.route, WebSocketRoute):
                route.route.solve(
                    dependencies=[
                        *dependencies,
                        *route.route.dependencies,
                    ],
                    container=self.container,
                )
        if not self._lifespans:
            # edge case: this app has no routes
            if self.lifespan is not None:
                self._lifespans.append(_wrap_lifespan_as_async_generator(self.lifespan))

    async def get_openapi(self) -> openapi_models.OpenAPI:
        return genrate_openapi(
            visitor=visit_routes(app_type=App, router=self.router, nodes=[self, self.router], path=""),  # type: ignore  # for Pylance
            version=self.openapi_version,
            info=self.openapi_info,
            servers=self.servers,
            security_models=await self.gather_security_models(),
        )

    async def gather_security_models(self) -> SecurityModels:
        security_dependants: typing.List[Security] = []
        for route in visit_routes(app_type=App, router=self.router, nodes=[self, self.router], path=""):  # type: ignore[misc]
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
