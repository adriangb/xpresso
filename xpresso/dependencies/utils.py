from __future__ import annotations

import typing

from di.api.container import ContainerProtocol
from starlette.background import BackgroundTasks
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket

from xpresso.dependencies.models import Dependant

T = typing.TypeVar("T")


def bind_framework_dependencies_to_container(container: ContainerProtocol):
    container.bind(
        Dependant(Request, scope="connection", wire=False),
        Request,
    )
    container.bind(
        Dependant(Request, scope="connection", wire=False),
        Request,
    )
    container.bind(
        Dependant(
            HTTPConnection,
            scope="connection",
            wire=False,
        ),
        HTTPConnection,
    )
    container.bind(
        Dependant(
            WebSocket,
            scope="connection",
            wire=False,
        ),
        WebSocket,
    )
    container.bind(
        Dependant(
            BackgroundTasks,
            scope="connection",
            wire=False,
        ),
        BackgroundTasks,
    )
