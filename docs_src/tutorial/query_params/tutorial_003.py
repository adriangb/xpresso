from typing import Optional

from xpresso import App, FromQuery, Path

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


async def read_item(skip: FromQuery[int] = 0, limit: FromQuery[Optional[int]] = 2):
    if limit is None:
        limit = len(fake_items_db)
    return fake_items_db[skip : skip + limit]


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_item,
        ),
    ]
)
