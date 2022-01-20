from xpresso import App, Dependant, FromHeader, WebSocket, WebSocketRoute
from xpresso.websockets import WebSocketDisconnect


async def enforce_header_pattern(x_header: FromHeader[str], ws: WebSocket) -> None:
    if not x_header.startswith("FooBarBaz: "):
        await ws.close()
        raise WebSocketDisconnect


async def websocket_endpoint(ws: WebSocket, x_header: FromHeader[str]) -> None:
    await ws.accept()
    await ws.send_text(x_header)
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
