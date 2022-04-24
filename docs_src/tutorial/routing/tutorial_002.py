from typing import List, Mapping

from pydantic import BaseModel

from xpresso import App, FromJson, Operation, Path, Response, Router
from xpresso.openapi.models import Server
from xpresso.responses import ResponseSpec
from xpresso.routing.mount import Mount


class Item(BaseModel):
    name: str
    price: float


fake_items_db = {
    "chair": Item(name="chair", price=30.29),
    "hammer": Item(name="hammer", price=1.99),
}


async def get_items() -> Mapping[str, Item]:
    """Docstring will be ignored"""
    return fake_items_db


async def create_item(item: FromJson[Item]) -> Response:
    """Documentation from docstrings!
    You can use any valid markdown, for example lists:

    - Point 1
    - Point 2
    """
    fake_items_db[item.name] = item
    return Response(status_code=204)


async def delete_items(items_to_delete: FromJson[List[str]]) -> None:
    for item_name in items_to_delete:
        fake_items_db.pop(item_name, None)


items = Path(
    "/items",
    get=Operation(
        get_items,
        description="The **items** operation",
        summary="List all items",
        deprecated=True,
        tags=["read"],
    ),
    post=Operation(
        create_item,
        responses={204: ResponseSpec(description="Success")},
        servers=[
            Server(url="https://us-east-1.example.com"),
            Server(url="http://127.0.0.1:8000"),
        ],
        tags=["write"],
    ),
    delete=Operation(
        delete_items,
        include_in_schema=False,
    ),
    include_in_schema=True,  # the default
    servers=[Server(url="http://127.0.0.1:8000")],
    tags=["items"],
)

app = App(
    routes=[
        Mount(
            path="/v1",
            app=Router(
                routes=[items],
                responses={
                    404: ResponseSpec(description="Item not found")
                },
                tags=["v1"],
            ),
        )
    ]
)
