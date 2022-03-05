from typing import Optional

from di.container._state import ContainerState
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket


class XpressoHTTPExtension:
    __slots__ = ("di_container_state", "request", "response", "response_sent")

    di_container_state: ContainerState
    request: Optional[Request]
    response: Optional[Response]
    response_sent: bool

    def __init__(self, di_state: ContainerState) -> None:
        self.di_container_state = di_state
        self.request = None
        self.response = None
        self.response_sent = False


class XpressoWebSocketExtension:
    __slots__ = ("di_container_state", "websocket")

    di_container_state: ContainerState
    websocket: Optional[WebSocket]

    def __init__(self, di_state: ContainerState) -> None:
        self.di_container_state = di_state
        self.websocket = None
