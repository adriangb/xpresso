from typing import List

from xpresso import App, Path, PathParam
from xpresso.typing import Annotated


async def read_items(
    items: Annotated[
        List[int], PathParam(explode=True, style="matrix")
    ]
) -> List[int]:
    return items


app = App(
    routes=[
        Path(
            path="/items/{items}",
            get=read_items,
        ),
    ]
)
