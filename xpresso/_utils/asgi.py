from typing import Optional

from di import BaseContainer
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket


class XpressoHTTPExtension:
    __slots__ = ("container", "request", "response", "response_sent")

    container: BaseContainer
    request: Optional[Request]
    response: Optional[Response]
    response_sent: bool

    def __init__(self, container: BaseContainer) -> None:
        self.container = container
        self.request = None
        self.response = None
        self.response_sent = False


class XpressoWebSocketExtension:
    __slots__ = ("container", "websocket")

    container: BaseContainer
    websocket: Optional[WebSocket]

    def __init__(self, container: BaseContainer) -> None:
        self.container = container
        self.websocket = None
