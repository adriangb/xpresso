from typing import Any

from pydantic import BaseModel

from xpresso import App, FromPath, Operation, Path
from xpresso.responses import JSONResponse, ResponseSpec


class Item(BaseModel):
    id: str
    value: str


class Message(BaseModel):
    message: str


async def read_item(item_id: FromPath[str]) -> Any:
    if item_id == "foo":
        return {"id": "foo", "value": "there goes my hero"}
    return JSONResponse(
        status_code=404, content={"message": "Item not found"}
    )


get_item = Operation(
    read_item,
    response_model=Item,
    responses={
        404: ResponseSpec(
            description="Item not found",
            content={"application/json": Message},
        )
    },
)

app = App(routes=[Path("/items/{item_id}", get=get_item)])
