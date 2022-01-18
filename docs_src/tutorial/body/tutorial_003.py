from typing import Dict, List

from xpresso import App, FromJson, Path


async def count_items(item_counts: FromJson[List[int]]) -> Dict[str, int]:
    return {"total": sum(item_counts)}


app = App(
    routes=[
        Path(
            "/items/count",
            put=count_items,
        )
    ]
)
