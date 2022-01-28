import typing
from dataclasses import dataclass

from starlette.routing import BaseRoute, Mount
from starlette.routing import Router as StarletteRouter

from xpresso.responses import Responses
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router as XpressoRouter


@dataclass(frozen=True)
class VisitedRoute:
    path: str
    routers: typing.List[StarletteRouter]
    route: BaseRoute
    tags: typing.List[str]
    responses: Responses


def visit_routes(
    routers: typing.List[StarletteRouter],
    path: typing.Optional[str] = None,
    tags: typing.Optional[typing.List[str]] = None,
    responses: typing.Optional[Responses] = None,
) -> typing.Generator[VisitedRoute, None, None]:
    path = path or ""
    tags = tags or []
    responses = responses or {}
    router = next(iter(reversed(routers)), None)
    assert router is not None
    for route in typing.cast(typing.Iterable[BaseRoute], router.routes):
        if isinstance(route, Mount) and isinstance(route.app, StarletteRouter):
            child_tags = tags
            child_responses = responses
            if isinstance(route.app, XpressoRouter):
                child_tags = child_tags + route.app.tags
                child_responses = {**child_responses, **route.app.responses}
            yield from visit_routes(
                routers=routers + [route.app],
                path=path + route.path,
                tags=child_tags,
                responses=child_responses,
            )
        elif hasattr(route, "path"):
            route_path: str = route.path  # type: ignore
            child_tags = tags
            child_responses = responses
            if isinstance(route, Path):
                child_tags = child_tags + route.tags
                child_responses = {**child_responses, **route.responses}
            yield VisitedRoute(
                path=path + route_path,
                routers=routers,
                route=route,
                tags=child_tags,
                responses=child_responses,
            )
