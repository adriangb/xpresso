import contextlib
import inspect
import typing

import starlette.types
from di.api.dependencies import DependantBase
from di.container import Container, ContainerState, bind_by_type
from di.dependant import Dependant, JoinedDependant
from di.executors import AsyncExecutor
from starlette.background import BackgroundTasks
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import BaseRoute
from starlette.routing import Route as StarletteRoute
from starlette.websockets import WebSocket

from xpresso._utils.asgi import XpressoHTTPExtension, XpressoWebSocketExtension
from xpresso._utils.overrides import DependencyOverrideManager
from xpresso._utils.routing import visit_routes
from xpresso.dependencies.models import Depends, Scopes
from xpresso.exception_handlers import (
    ExcHandler,
    http_exception_handler,
    validation_exception_handler,
)
from xpresso.exceptions import RequestValidationError
from xpresso.middleware.exceptions import ExceptionMiddleware
from xpresso.openapi import models as openapi_models
from xpresso.openapi._builder import genrate_openapi
from xpresso.openapi._html import get_swagger_ui_html
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router
from xpresso.routing.websockets import WebSocketRoute


class App:
    router: Router
    container: Container
    dependency_overrides: DependencyOverrideManager

    __slots__ = (
        "_container_state",
        "_debug",
        "_openapi_info",
        "_openapi_servers",
        "_openapi_version",
        "_openapi",
        "_root_path",
        "_root_path_in_servers",
        "_setup_run",
        "container",
        "dependency_overrides",
        "router",
    )

    def __init__(
        self,
        routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
        *,
        container: typing.Optional[Container] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]]
        ] = None,
        debug: bool = False,
        middleware: typing.Optional[typing.Sequence[Middleware]] = None,
        exception_handlers: typing.Optional[typing.Iterable[ExcHandler]] = None,
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
        root_path: str = "",
        root_path_in_servers: bool = True,
    ) -> None:
        self.container = container or Container()
        _register_framework_dependencies(self.container, app=self)
        self.dependency_overrides = DependencyOverrideManager(self.container)
        self._container_state: ContainerState = ContainerState()
        self._setup_run = False

        @contextlib.asynccontextmanager
        async def lifespan_ctx(*_: typing.Any) -> typing.AsyncIterator[None]:
            lifespans, lifespan_deps = self._setup()
            self._setup_run = True
            original_container = self.container
            async with self._container_state.enter_scope(
                "app"
            ) as self._container_state:
                if lifespan is not None:
                    dep = Dependant(
                        _wrap_lifespan_as_async_generator(lifespan), scope="app"
                    )
                else:

                    async def null_lifespan() -> typing.AsyncIterator[None]:
                        yield

                    dep = Dependant(null_lifespan, scope="app")
                solved = self.container.solve(
                    JoinedDependant(
                        dep,
                        siblings=[
                            *(
                                Dependant(lifespan, scope="app")
                                for lifespan in lifespans
                            ),
                            *lifespan_deps,
                        ],
                    ),
                    scopes=Scopes,
                )
                try:
                    await self.container.execute_async(
                        solved, executor=AsyncExecutor(), state=self._container_state
                    )
                    yield
                finally:
                    # make this cm reentrant for testing purposes
                    self.container = original_container
                    self._setup_run = False
                    self._container_state = ContainerState()

        self._debug = debug

        routes = list(routes or [])
        routes.extend(
            self._get_doc_routes(
                openapi_url=openapi_url,
                docs_url=docs_url,
            )
        )
        middleware = _build_middleware_stack(
            debug=debug,
            user_middleware=middleware or (),
            exception_handlers=exception_handlers or (),
        )
        self.router = Router(
            routes,
            dependencies=dependencies,
            middleware=middleware,
            include_in_schema=include_in_schema,
            lifespan=lifespan_ctx,
        )

        self._openapi_version = openapi_version
        self._openapi_info = openapi_models.Info(
            title=title,
            version=version,
            description=description,
        )
        self._openapi_servers = servers or []
        self._openapi: "typing.Optional[typing.Dict[str, typing.Any]]" = None
        self._root_path_in_servers = root_path_in_servers
        self._root_path = root_path

    async def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> None:
        if self._root_path:
            prefix = scope.get("root_path", None)
            if prefix:
                scope["root_path"] = prefix.rstrip("/") + self._root_path
            else:
                scope["root_path"] = self._root_path
        scope_type = scope["type"]
        if scope_type == "lifespan":
            await self.router(scope, receive, send)
            return
        # http or websocket
        if not self._setup_run:
            self._setup()
        if "extensions" not in scope:
            scope["extensions"] = extensions = {}
        else:
            extensions = scope["extensions"]
        if scope_type == "http":
            if "xpresso" not in extensions:
                extensions["xpresso"] = XpressoHTTPExtension(
                    di_state=self._container_state
                )
        else:  # websocket
            if "xpresso" not in extensions:
                extensions["xpresso"] = XpressoWebSocketExtension(
                    di_state=self._container_state
                )
        await self.router(scope, receive, send)

    def _setup(
        self,
    ) -> typing.Tuple[
        typing.List[typing.Callable[..., typing.AsyncIterator[None]]],
        typing.List[DependantBase[typing.Any]],
    ]:
        lifespans: typing.List[typing.Callable[..., typing.AsyncIterator[None]]] = []
        lifespan_dependants: typing.List[DependantBase[typing.Any]] = []
        seen_routers: typing.Set[typing.Any] = set()
        for route in visit_routes(
            app_type=App, router=self.router, nodes=[self, self.router], path=""
        ):
            dependencies: typing.List[DependantBase[typing.Any]] = []
            for node in route.nodes:
                if isinstance(node, Router):
                    dependencies.extend(node.dependencies)
                    if node in seen_routers:
                        continue
                    seen_routers.add(node)
                    # avoid circular lifespan calls
                    if node is not self.router and node.lifespan is not None:
                        lifespans.append(
                            _wrap_lifespan_as_async_generator(node.lifespan)
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
                    for dep in operation.dependant.get_flat_subdependants():
                        if dep.scope == "app":
                            lifespan_dependants.append(dep)
            elif isinstance(route.route, WebSocketRoute):
                route.route.solve(
                    dependencies=[
                        *dependencies,
                        *route.route.dependencies,
                    ],
                    container=self.container,
                )
                for dep in route.route.dependant.get_flat_subdependants():
                    if dep.scope == "app":
                        lifespan_dependants.append(dep)
        return lifespans, lifespan_dependants

    def get_openapi(
        self, servers: typing.List[openapi_models.Server]
    ) -> openapi_models.OpenAPI:
        return genrate_openapi(
            visitor=visit_routes(
                app_type=App, router=self.router, nodes=[self, self.router], path=""
            ),
            container=self.container,
            version=self._openapi_version,
            info=self._openapi_info,
            servers=servers,
        )

    def _get_doc_routes(
        self,
        openapi_url: typing.Optional[str],
        docs_url: typing.Optional[str],
    ) -> typing.Iterable[BaseRoute]:
        routes: typing.List[BaseRoute] = []

        if openapi_url:
            openapi_url = openapi_url

            async def openapi(req: Request) -> JSONResponse:
                # get the root_path from the request and not just App._root_path
                # so that we can use the value set by the ASGI server
                # since ASGI servers also let you configure this
                root_path: str = req.scope.get("root_path", "").rstrip("/")  # type: ignore
                if self._openapi is None:
                    servers = list(self._openapi_servers)
                    if self._root_path_in_servers and root_path:
                        server_urls = {s.url for s in servers}
                        if root_path not in server_urls:
                            servers.insert(0, openapi_models.Server(url=root_path))
                    self._openapi = self.get_openapi(servers=servers).dict(
                        exclude_none=True, by_alias=True
                    )
                return JSONResponse(self._openapi)

            routes.append(
                StarletteRoute(
                    path=openapi_url, endpoint=openapi, include_in_schema=False
                )
            )
        if openapi_url and docs_url:

            openapi_url = openapi_url

            async def swagger_ui_html(req: Request) -> HTMLResponse:
                # see above for note on why we get root_path from the request
                root_path: str = req.scope.get("root_path", "").rstrip("/")  # type: ignore  # for Pylance
                full_openapi_url = root_path + openapi_url  # type: ignore[operator]
                return get_swagger_ui_html(
                    openapi_url=full_openapi_url,
                    title=f"{self._openapi_info.title} - Swagger UI",
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


def _build_middleware_stack(
    debug: bool,
    user_middleware: typing.Iterable[Middleware],
    exception_handlers: typing.Iterable[ExcHandler],
) -> typing.Sequence[Middleware]:
    # user's exception handlers come last so that they can override
    # the default exception handlers
    exception_handlers = [
        ExcHandler(RequestValidationError, validation_exception_handler),
        ExcHandler(HTTPException, http_exception_handler),
        *exception_handlers,
    ]

    exc_handler_mapping: typing.Dict[typing.Any, typing.Any] = {}

    error_handler = None
    for hdlr in exception_handlers:
        if hdlr.exc in (500, Exception):
            error_handler = hdlr.handler
        else:
            exc_handler_mapping[hdlr.exc] = hdlr.handler

    return (
        Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug),
        *user_middleware,
        Middleware(ExceptionMiddleware, handlers=exc_handler_mapping, debug=debug),
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


def _register_framework_dependencies(container: Container, app: App):
    container.bind(
        bind_by_type(
            Dependant(Request, scope="connection", wire=False),
            Request,
        )
    )
    container.bind(
        bind_by_type(
            Dependant(
                HTTPConnection,
                scope="connection",
                wire=False,
            ),
            HTTPConnection,
        )
    )
    container.bind(
        bind_by_type(
            Dependant(
                WebSocket,
                scope="connection",
                wire=False,
            ),
            WebSocket,
        )
    )
    container.bind(
        bind_by_type(
            Dependant(
                BackgroundTasks,
                scope="connection",
                wire=False,
            ),
            BackgroundTasks,
        )
    )
    container.bind(
        bind_by_type(
            Dependant(
                lambda: app.container,
                scope="app",
                wire=False,
            ),
            Container,
            covariant=True,
        )
    )
    container.bind(
        bind_by_type(
            Dependant(
                lambda: app,
                scope="app",
                wire=False,
            ),
            App,
            covariant=True,
        )
    )
