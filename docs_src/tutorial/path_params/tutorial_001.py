from typing import Dict

from xpresso import App, FromPath, Path


async def read_item(item_id: FromPath[str]) -> Dict[str, str]:
    return {"item_id": item_id}


app = App(
    routes=[
        Path(
            path="/items/{item_id}",
            get=read_item,
        ),
    ]
)
