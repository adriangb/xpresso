from typing import Optional

from pydantic import BaseModel

from xpresso import App, Path, QueryParam
from xpresso.typing import Annotated


class Filter(BaseModel):
    prefix: str
    limit: int
    skip: int = 0


async def read_items(
    filter: Annotated[Optional[Filter], QueryParam(style="deepObject")]
) -> Optional[Filter]:
    return filter


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_items,
        ),
    ]
)
