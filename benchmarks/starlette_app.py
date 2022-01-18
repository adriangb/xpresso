from starlette.applications import Starlette as App
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route


async def simple(request: Request) -> Response:
    """An endpoint that does the minimal amount of work"""
    return Response()


app = App(routes=[Route("/simple", simple)])
