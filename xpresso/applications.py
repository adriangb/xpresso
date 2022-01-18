import typing
from contextlib import asynccontextmanager

import starlette.types as asgi
from di import AsyncExecutor, BaseContainer
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProviderType
from starlette.applications import Starlette
from starlette.datastructures import State
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.routing import Route as StarletteRoute

from xpresso._utils.routing import get_path_params, visit_routes
from xpresso.dependencies.models import Dependant
from xpresso.dependencies.utils import register_framework_dependencies
from xpresso.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
)
from xpresso.exceptions import RequestValidationError
from xpresso.openapi import models as openapi_models
from xpresso.openapi._builder import SecurityModels, genrate_openapi
from xpresso.openapi._html import get_swagger_ui_html
from xpresso.routing import APIRouter, Path
from xpresso.security._dependants import Security

ExceptionHandler = typing.Callable[[Request, typing.Type[BaseException]], Response]


class App(Starlette):
    router: APIRouter
    middleware_stack: asgi.ASGIApp
    openapi: typing.Optional[openapi_models.OpenAPI] = None
    _debug: bool
    state: State
    exception_handlers: typing.Mapping[
        typing.Union[int, typing.Type[Exception]], ExceptionHandler
    ]
    user_middleware: typing.Sequence[Middleware]

    def __init__(
        self,
        routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
        *,
        container: typing.Optional[BaseContainer] = None,
        dependencies: typing.Optional[typing.List[Dependant]] = None,
        debug: bool = False,
        middleware: typing.Optional[typing.Sequence[Middleware]] = None,
        exception_handlers: typing.Optional[
            typing.Dict[
                typing.Union[int, typing.Type[Exception]],
                ExceptionHandler,
            ]
        ] = None,
        lifespan: typing.Optional[DependencyProviderType[None]] = None,
        openapi_version: str = "3.0.3",
        title: str = "API",
        description: typing.Optional[str] = None,
        version: str = "0.1.0",
        openapi_url: typing.Optional[str] = "/openapi.json",
        docs_url: typing.Optional[str] = "/docs"
    ) -> None:
        routes = list(routes or [])
        routes.extend(
            self._get_doc_routes(
                openapi_url=openapi_url,
                docs_url=docs_url,
            )
        )
        self._debug = debug
        self.state = State()
        self.exception_handlers = (
            {} if exception_handlers is None else dict(exception_handlers)
        )

        self.container = container or BaseContainer(
            scopes=("app", "connection", "endpoint")
        )
        register_framework_dependencies(self.container)
        if lifespan is not None:
            solved_lifespan = self.container.solve(
                Dependant(call=lifespan, scope="app")
            )
        else:
            solved_lifespan = None
        self._setup_run = False

        @asynccontextmanager
        async def lifespan_ctx(app: Starlette) -> typing.AsyncGenerator[None, None]:
            self._setup()
            self._setup_run = True
            original_container = self.container
            async with self.container.enter_scope("app") as container:
                self.container = container
                if solved_lifespan is not None:
                    await container.execute_async(
                        solved_lifespan, executor=AsyncExecutor()
                    )
                try:
                    yield
                finally:
                    self.container = original_container
                    self._setup_run = False

        self.router = APIRouter(
            routes, lifespan=lifespan_ctx, dependencies=dependencies
        )
        self.user_middleware = [] if middleware is None else list(middleware)
        self.middleware_stack = self.build_middleware_stack()  # type: ignore
        self.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
        self.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
        self.openapi_version = openapi_version
        self.openapi_info = openapi_models.Info(
            title=title,
            version=version,
            description=description,
        )

    async def __call__(
        self, scope: asgi.Scope, receive: asgi.Receive, send: asgi.Send
    ) -> None:
        self._setup()
        if scope["type"] == "http":
            extensions = scope.get("extensions", None) or {}
            xpresso_scope = extensions.get("xpresso", None)
            if xpresso_scope is None:
                async with self.container.enter_scope("connection") as container:
                    extensions["xpresso"] = {"container": container}
                    scope["extensions"] = extensions
                    return await super().__call__(scope, receive, send)
        return await super().__call__(scope, receive, send)

    def _setup(self) -> None:
        if self._setup_run:
            return
        for route in visit_routes([self.router]):
            dependencies: typing.List[DependantBase[typing.Any]] = []
            for router in route.routers:
                if isinstance(router, APIRouter):
                    dependencies.extend(router.dependencies)
            if isinstance(route.route, Path):
                for operation in route.route.operations.values():
                    operation.solve(
                        path_params=get_path_params(route.path),
                        dependencies=[
                            *dependencies,
                            *route.route.dependencies,
                            *operation.dependencies,
                        ],
                        container=self.container,
                    )

    async def get_openapi(self) -> openapi_models.OpenAPI:
        return genrate_openapi(
            version=self.openapi_version,
            info=self.openapi_info,
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
                root_path: str = req.scope.get("root_path", "").rstrip("/")
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
