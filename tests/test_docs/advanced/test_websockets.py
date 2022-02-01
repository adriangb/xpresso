import pytest

from docs_src.advanced.websockets import app
from xpresso.exceptions import WebSocketValidationError
from xpresso.testclient import TestClient
from xpresso.websockets import WebSocketDisconnect


def test_websockets_missing_header() -> None:
    client = TestClient(app)

    with pytest.raises(WebSocketValidationError) as err:
        with client.websocket_connect("/ws"):
            pass

    assert isinstance(err.value, WebSocketValidationError)
    assert err.value.errors() == [{'loc': ('header', 'x_header'), 'msg': 'Missing required header parameter', 'type': 'value_error'}]


def test_websockets_unprocessable_header() -> None:
    client = TestClient(app)

    with pytest.raises(WebSocketValidationError) as err:
        with client.websocket_connect("/ws", headers={"X-Header": "not a number"}):
            pass

    assert isinstance(err.value, WebSocketValidationError)
    assert err.value.errors() == [{'loc': ('header', 'x_header'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]


def test_websockets_exception_in_user_dependency() -> None:
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws", headers={"X-Header": "-1"}):
            raise AssertionError("Should not be called")  # pragma: no cover
    except WebSocketDisconnect:
        pass
    else:
        raise AssertionError(
            "Expected a WebSocketDisconnect to be raised"
        )  # pragma: no cover


def test_websockets_valid_header() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws", headers={"X-Header": "123"}) as websocket:
        data = websocket.receive_text()
        assert data == "123"
