from docs_src.advanced.websockets import app
from xpresso.testclient import TestClient
from xpresso.websockets import WebSocketDisconnect


def test_websockets() -> None:
    client = TestClient(app)

    # missing header
    try:
        with client.websocket_connect("/ws"):
            raise AssertionError("Should not be called")  # pragma: no cover
    except WebSocketDisconnect:
        pass
    else:
        raise AssertionError(
            "Expected a WebSocketDisconnect to be raised"
        )  # pragma: no cover

    # wrong header
    try:
        with client.websocket_connect(
            "/ws", headers={"X-Header": "BarBaz: placeholder"}
        ):
            raise AssertionError("Should not be called")  # pragma: no cover
    except WebSocketDisconnect:
        pass
    else:
        raise AssertionError(
            "Expected a WebSocketDisconnect to be raised"
        )  # pragma: no cover

    # valid header
    with client.websocket_connect(
        "/ws", headers={"X-Header": "FooBarBaz: placeholder"}
    ) as websocket:
        data = websocket.receive_text()
        assert data == "FooBarBaz: placeholder"
