from pydantic import BaseModel

from xpresso import App, Operation, Path, status


class Item(BaseModel):
    id: str
    value: str


async def create_item(item: Item) -> None:
    ...


post_item = Operation(
    create_item,
    response_status_code=status.HTTP_204_NO_CONTENT,
)

app = App(routes=[Path("/items/", post=post_item)])
