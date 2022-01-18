import typing
from dataclasses import dataclass

from starlette.routing import BaseRoute, Mount, Router, compile_path


@dataclass(frozen=True)
class VisitedRoute:
    path: str
    routers: typing.List[Router]
    route: BaseRoute


def visit_routes(
    routers: typing.List[Router], path: typing.Optional[str] = None
) -> typing.Generator[VisitedRoute, None, None]:
    path = path or ""
    router = next(iter(reversed(routers)), None)
    assert router is not None
    for route in typing.cast(typing.Iterable[BaseRoute], router.routes):
        if isinstance(route, Mount) and isinstance(route.app, Router):
            yield from visit_routes(routers + [route.app], path + route.path)
        elif hasattr(route, "path"):
            yield VisitedRoute(path + getattr(route, "path"), routers, route)


def get_path_params(path: str) -> typing.Set[str]:
    *_, converters = compile_path(path)
    return set(converters.keys())
