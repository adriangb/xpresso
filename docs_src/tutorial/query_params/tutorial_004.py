from typing import List

from xpresso import App, FromQuery, Path

fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
]


async def read_item(prefix: FromQuery[List[str]]):
    return [
        item
        for item in fake_items_db
        if all(item["item_name"].startswith(p) for p in prefix or [])
    ]


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_item,
        ),
    ]
)
