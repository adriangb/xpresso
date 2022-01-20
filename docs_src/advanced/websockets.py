from xpresso import App, Dependant, FromHeader, WebSocket, WebSocketRoute
from xpresso.exceptions import WebSocketValidationError


async def enforce_header_pattern(x_header: FromHeader[int], ws: WebSocket) -> None:
    if not x_header > 0:
        await ws.close()
        # This currently produces a 500 error in the server logs
        # See https://github.com/encode/starlette/pull/527 for more info
        raise WebSocketValidationError([])


async def websocket_endpoint(ws: WebSocket, x_header: FromHeader[int]) -> None:
    await ws.accept()
    await ws.send_text(str(x_header))
    await ws.close()


app = App(
    routes=[
        WebSocketRoute(
            path="/ws",
            endpoint=websocket_endpoint,
            dependencies=[Dependant(enforce_header_pattern)],
        ),
    ]
)
