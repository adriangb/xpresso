from typing import Optional

from di.container._state import ContainerState
from starlette.responses import Response


class XpressoHTTPExtension:
    __slots__ = ("di_container_state", "response", "response_sent")

    di_container_state: ContainerState
    response: Optional[Response]
    response_sent: bool

    def __init__(self, di_state: ContainerState) -> None:
        self.di_container_state = di_state
        self.response = None
        self.response_sent = False


class XpressoWebSocketExtension:
    __slots__ = ("di_container_state",)

    di_container_state: ContainerState

    def __init__(self, di_state: ContainerState) -> None:
        self.di_container_state = di_state
