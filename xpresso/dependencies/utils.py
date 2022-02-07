from __future__ import annotations

import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from di import BaseContainer
from starlette.background import BackgroundTasks
from starlette.requests import HTTPConnection, Request
from starlette.websockets import WebSocket

from xpresso.dependencies.models import Depends


class App(Protocol):
    @property
    def container(self) -> BaseContainer:
        ...


def register_framework_dependencies(
    container: BaseContainer, app: App, app_type: typing.Type[App]
):
    container.register_by_type(
        Depends(Request, scope="connection", wire=False),
        Request,
    )
    container.register_by_type(
        Depends(Request, scope="connection", wire=False),
        Request,
    )
    container.register_by_type(
        Depends(
            HTTPConnection,
            scope="connection",
            wire=False,
        ),
        HTTPConnection,
    )
    container.register_by_type(
        Depends(
            WebSocket,
            scope="connection",
            wire=False,
        ),
        WebSocket,
    )
    container.register_by_type(
        Depends(
            lambda: BackgroundTasks(),
            scope="connection",
            wire=False,
        ),
        BackgroundTasks,
    )
    container.register_by_type(
        Depends(
            lambda: app.container,
            scope="app",
            wire=False,
        ),
        BaseContainer,
        covariant=True,
    )
    container.register_by_type(
        Depends(
            lambda: app,
            scope="app",
            wire=False,
        ),
        app_type,
        covariant=True,
    )
