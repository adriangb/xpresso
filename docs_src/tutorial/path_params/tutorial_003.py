from typing import Dict

from pydantic import Field

from xpresso import App, Path, PathParam
from xpresso.typing import Annotated


async def read_item(
    item_id: Annotated[int, PathParam(), Field(gt=0)]
) -> Dict[str, int]:
    return {"item_id": item_id}


app = App(
    routes=[
        Path(
            path="/items/{item_id}",
            get=read_item,
        ),
    ]
)
