import typing
from dataclasses import dataclass

from starlette.routing import BaseRoute, Mount
from starlette.routing import Router as StarletteRouter

from xpresso._utils.compat import Protocol
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router as XpressoRouter
from xpresso.routing.websockets import WebSocketRoute

Router = typing.Union[XpressoRouter, StarletteRouter]


class App(Protocol):
    @property
    def router(self) -> XpressoRouter:
        ...


AppType = typing.TypeVar("AppType", bound=App)


@dataclass(frozen=True)
class VisitedRoute(typing.Generic[AppType]):
    path: str
    nodes: typing.List[typing.Union[Router, AppType]]
    route: BaseRoute


def visit_routes(
    app_type: typing.Type[AppType],
    router: Router,
    nodes: typing.List[typing.Union[Router, AppType]],
    path: str,
) -> typing.Generator[VisitedRoute[AppType], None, None]:
    for route in typing.cast(typing.Iterable[BaseRoute], router.routes):  # type: ignore  # for Pylance
        if isinstance(route, Mount):
            app: typing.Any = route.app
            mount_path: str = route.path  # type: ignore  # for Pylance
            if isinstance(app, (StarletteRouter, XpressoRouter)):
                yield VisitedRoute(
                    path=path,
                    nodes=nodes + [app],
                    route=route,
                )
                yield from visit_routes(
                    app_type=app_type,
                    router=app,
                    nodes=nodes + [app],
                    path=path + mount_path,
                )
            elif isinstance(app, app_type):
                yield VisitedRoute(
                    path=path,
                    nodes=nodes + [app, app.router],
                    route=route,
                )
                yield from visit_routes(
                    app_type=app_type,
                    router=app.router,
                    nodes=nodes + [app, app.router],
                    path=path + mount_path,
                )
        elif isinstance(route, (Path, WebSocketRoute)):
            yield VisitedRoute(
                path=path + route.path,
                nodes=nodes,
                route=route,
            )
