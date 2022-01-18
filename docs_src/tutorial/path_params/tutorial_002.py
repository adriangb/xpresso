from typing import Dict

from xpresso import App, FromPath, Path


async def read_item(item_id: FromPath[int]) -> Dict[str, int]:
    return {"item_id": item_id}


app = App(
    routes=[
        Path(
            path="/items/{item_id}",
            get=read_item,
        ),
    ]
)
