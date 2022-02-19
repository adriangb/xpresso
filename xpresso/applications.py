import contextlib
import inspect
import typing

import starlette.types
from di import AsyncExecutor, BaseContainer, JoinedDependant
from di.api.dependencies import DependantBase
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.routing import Route as StarletteRoute
from starlette.websockets import WebSocket

from xpresso._utils.asgi_scope_extension import XpressoASGIExtension
from xpresso._utils.overrides import DependencyOverrideManager
from xpresso._utils.routing import visit_routes
from xpresso.dependencies.models import Depends
from xpresso.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from xpresso.exceptions import HTTPException, RequestValidationError
from xpresso.middleware.exceptions import ExceptionMiddleware
from xpresso.openapi import models as openapi_models
from xpresso.openapi._builder import genrate_openapi
from xpresso.openapi._html import get_swagger_ui_html
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router
from xpresso.routing.websockets import WebSocketRoute

ExceptionHandler = typing.Callable[
    [Request, Exception], typing.Union[Response, typing.Awaitable[Response]]
]
ExceptionHandlers = typing.Mapping[
    typing.Union[typing.Type[Exception], int], ExceptionHandler
]

_REQUIRED_CONTAINER_SCOPES = ("app", "connection", "endpoint")


class App:
    router: Router
    container: BaseContainer
    dependency_overrides: DependencyOverrideManager

    __slots__ = (
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
        container: typing.Optional[BaseContainer] = None,
        dependencies: typing.Optional[typing.List[DependantBase[typing.Any]]] = None,
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
        root_path: str = "",
        root_path_in_servers: bool = True,
    ) -> None:
        if container is not None:
            if tuple(container.scopes) != _REQUIRED_CONTAINER_SCOPES:
                raise ValueError(
                    f"Containers must have exactly the following scopes (in order): {_REQUIRED_CONTAINER_SCOPES}"
                )
            self.container = container
        else:
            self.container = BaseContainer(scopes=_REQUIRED_CONTAINER_SCOPES)
        _register_framework_dependencies(self.container, app=self)
        self.dependency_overrides = DependencyOverrideManager(self.container)
        self._setup_run = False

        @contextlib.asynccontextmanager
        async def lifespan_ctx(*_: typing.Any) -> typing.AsyncIterator[None]:
            lifespans, lifespan_deps = self._setup()
            self._setup_run = True
            original_container = self.container
            async with self.container.enter_scope("app") as container:
                self.container = container
                if lifespan is not None:
                    dep = Depends(
                        _wrap_lifespan_as_async_generator(lifespan), scope="app"
                    )
                else:
                    dep = Depends(lambda: None, scope="app")
                solved = self.container.solve(
                    JoinedDependant(
                        dep,
                        siblings=[
                            *(Depends(lifespan, scope="app") for lifespan in lifespans),
                            *lifespan_deps,
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
        if scope_type in ["http", "websocket"]:
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


def _register_framework_dependencies(container: BaseContainer, app: App):
    container.bind_by_type(
        Depends(Request, scope="connection", wire=False),
        Request,
    )
    container.bind_by_type(
        Depends(
            HTTPConnection,
            scope="connection",
            wire=False,
        ),
        HTTPConnection,
    )
    container.bind_by_type(
        Depends(
            WebSocket,
            scope="connection",
            wire=False,
        ),
        WebSocket,
    )
    container.bind_by_type(
        Depends(
            BackgroundTasks,
            scope="connection",
            wire=False,
        ),
        BackgroundTasks,
    )
    container.bind_by_type(
        Depends(
            lambda: app.container,
            scope="app",
            wire=False,
        ),
        BaseContainer,
        covariant=True,
    )
    container.bind_by_type(
        Depends(
            lambda: app,
            scope="app",
            wire=False,
        ),
        App,
        covariant=True,
    )
