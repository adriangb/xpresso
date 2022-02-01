import inspect
import typing
from contextlib import asynccontextmanager

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
            scopes=("app", "connection", "endpoint")
        )
        register_framework_dependencies(self.container)
        self._setup_run = False

        @asynccontextmanager
        async def lifespan_ctx(*args: typing.Any) -> typing.AsyncIterator[None]:
            lifespans = self._setup()
            self._setup_run = True
            original_container = self.container
            async with self.container.enter_scope("app") as container:
                self.container = container
                if lifespan is not None:
                    dep = Dependant(
                        _wrap_lifespan_as_async_generator(lifespan), scope="app"
                    )
                else:
                    dep = Dependant(lambda: None, scope="app")
                solved = self.container.solve(
                    JoinedDependant(
                        dep,
                        siblings=[
                            Dependant(lifespan, scope="app") for lifespan in lifespans
                        ],
                    )
                )
                try:
                    await container.execute_async(solved, executor=AsyncExecutor())
                    yield
                finally:
                    # make this cm reentrant for testing purposes
                    self.container = original_container
                    self._setup_run = False

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
            lifespan=lifespan_ctx,
        )

        self.openapi_version = openapi_version
        self.openapi_info = openapi_models.Info(
            title=title,
            version=version,
            description=description,
        )
        self.servers = servers
        self.openapi = None

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
            await self.router(scope, receive, send)

    def _setup(self) -> typing.List[typing.Callable[..., typing.AsyncIterator[None]]]:
        lifespans: typing.List[typing.Callable[..., typing.AsyncIterator[None]]] = []
        for route in visit_routes(
            app_type=App, router=self.router, nodes=[self, self.router], path=""
        ):
            dependencies: typing.List[DependantBase[typing.Any]] = []
            for node in route.nodes:
                if isinstance(node, Router):
                    dependencies.extend(node.dependencies)
                    if node is not self.router:  # avoid circul lifespan calls
                        lifespan = typing.cast(
                            typing.Callable[..., typing.AsyncContextManager[None]],
                            node.lifespan_context,  # type: ignore  # for Pylance
                        )
                        if lifespan is not None:
                            lifespans.append(
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
        return lifespans

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
