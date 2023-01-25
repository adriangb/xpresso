from typing import Optional

from di import ScopeState
from starlette.responses import Response


class XpressoHTTPExtension:
    __slots__ = ("di_container_state", "response", "response_sent")

    di_container_state: ScopeState
    response: Optional[Response]
    response_sent: bool

    def __init__(self, di_state: ScopeState) -> None:
        self.di_container_state = di_state
        self.response = None
        self.response_sent = False


class XpressoWebSocketExtension:
    __slots__ = ("di_container_state",)

    di_container_state: ScopeState

    def __init__(self, di_state: ScopeState) -> None:
        self.di_container_state = di_state
