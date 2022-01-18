from pydantic import Field

from xpresso import App, Path, QueryParam
from xpresso.typing import Annotated

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


async def read_item(
    skip: Annotated[
        int,
        QueryParam(description="Count of items to skip starting from the 0th item"),
        Field(gt=0),
    ],
    limit: Annotated[
        int,
        QueryParam(),
        Field(gt=0, description="Maximum number of items to return"),
    ],
):
    return fake_items_db[skip : skip + limit]


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_item,
        ),
    ]
)
