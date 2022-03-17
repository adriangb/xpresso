from xpresso import App, FromPath, Operation, Path, Response


async def read_item(item_id: FromPath[str]) -> bytes:
    return f"<bytes from {item_id}.png>".encode()


get_item = Operation(
    read_item,
    response_media_type="image/png",
    response_encoder=None,
    response_factory=Response,
)

app = App(routes=[Path("/items/{item_id}", get=get_item)])
