import pytest

from docs_src.advanced.websockets import app
from xpresso.testclient import TestClient
from xpresso.websockets import WebSocketDisconnect


def test_websockets() -> None:
    client = TestClient(app)

    # missing header
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws"):
            pass

    # wrong header
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws", headers={"X-Header": "BarBaz: placeholder"}
        ):
            pass

    # valid header
    with client.websocket_connect(
        "/ws", headers={"X-Header": "FooBarBaz: placeholder"}
    ) as websocket:
        data = websocket.receive_text()
        assert data == "FooBarBaz: placeholder"
