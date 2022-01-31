from typing import Awaitable, List, Mapping, Union
from starlette.applications import Starlette as App
from starlette.responses import Response
from starlette.routing import Route, Router, Mount, BaseRoute
from starlette.types import Scope, Receive, Send

from benchmarks.constants import ROUTING_PATHS

class Simple:
    def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
        return Response()(scope, receive, send)


Paths = Mapping[str, Union["Paths", None]]  # type: ignore[misc]


def recurisively_generate_routes(paths: Paths) -> Router:
    routes: List[BaseRoute] = []
    for path in paths:
        subpaths = paths[path]
        if subpaths is None:
            routes.append(Route(f"/{path}", Simple()))
        else:
            routes.append(Mount(f"/{path}", app=recurisively_generate_routes(subpaths)))
    return Router(routes=routes)


app = App(routes=[Route("/simple", Simple()), Mount("/routing", app=recurisively_generate_routes(ROUTING_PATHS))])
