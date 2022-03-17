from pydantic import BaseModel

from xpresso import App, FromPath, HTTPException, Path
from xpresso.responses import ResponseSpec


class Item(BaseModel):
    id: str
    value: str


async def read_item(item_id: FromPath[str]) -> Item:
    if item_id == "foo":
        return Item(id="foo", value="there goes my hero")
    raise HTTPException(status_code=404)


app = App(
    routes=[
        Path(
            "/items/{item_id}",
            get=read_item,
            responses={
                404: ResponseSpec(
                    description="Item not found",
                )
            },
        )
    ]
)
