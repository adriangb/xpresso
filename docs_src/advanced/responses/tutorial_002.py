from typing import Any, Optional

from pydantic import BaseModel

from xpresso import App, FromPath, Operation, Path
from xpresso.parameters import FromQuery
from xpresso.responses import Response, ResponseSpec


class Item(BaseModel):
    id: str
    value: str


async def read_item(
    item_id: FromPath[str], img: FromQuery[Optional[bool]]
) -> Any:
    if img:
        return Response(b"<image bytes>", media_type="image/png")
    else:
        return {"id": "foo", "value": "there goes my hero"}


get_item = Operation(
    read_item,
    responses={
        200: ResponseSpec(
            description="Successful Response",
            content={"application/json": Item, "image/png": bytes},
        )
    },
)

app = App(routes=[Path("/items/{item_id}", get=get_item)])
