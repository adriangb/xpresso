import re
from typing import List

from xpresso import App, Path, QueryParam
from xpresso.openapi.models import Example
from xpresso.typing import Annotated

fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
]


prefix_examples = {
    "Starts with Foo": Example(value="Foo.*"),
    "Starts with Foo or Bar": Example(value="Foo.*|Bar.*"),
}

QueryFilter = Annotated[
    str,
    QueryParam(
        description="Regular expression to filter items by name",
        examples=prefix_examples,
    ),
]


async def read_item(filter: QueryFilter) -> List[str]:
    return [
        item["item_name"]
        for item in fake_items_db
        if re.match(filter, item["item_name"])
    ]


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_item,
        ),
    ]
)
