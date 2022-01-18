from xpresso import App, FromQuery, Path

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


async def read_items(skip: FromQuery[int] = 0, limit: FromQuery[int] = 2):
    return fake_items_db[skip : skip + limit]


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_items,
        ),
    ]
)
