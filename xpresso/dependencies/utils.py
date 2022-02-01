from __future__ import annotations

import typing

from di import BaseContainer
from starlette.background import BackgroundTasks
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket

from xpresso.dependencies.models import Dependant

T = typing.TypeVar("T")


def register_framework_dependencies(container: BaseContainer, app: typing.Any):
    container.register_by_type(
        Dependant(Request, scope="connection", wire=False),
        Request,
    )
    container.register_by_type(
        Dependant(Request, scope="connection", wire=False),
        Request,
    )
    container.register_by_type(
        Dependant(
            HTTPConnection,
            scope="connection",
            wire=False,
        ),
        HTTPConnection,
    )
    container.register_by_type(
        Dependant(
            WebSocket,
            scope="connection",
            wire=False,
        ),
        WebSocket,
    )
    container.register_by_type(
        Dependant(
            BackgroundTasks,
            scope="connection",
            wire=False,
        ),
        BackgroundTasks,
    )
    container.register_by_type(
        Dependant(
            lambda: app,
            scope="app",
            wire=False,
        ),
        type(app),
    )
