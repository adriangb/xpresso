from typing import Dict, Optional

from pydantic import BaseModel

from xpresso import App, Json, Path
from xpresso.typing import Annotated


class Item(BaseModel):
    name: str
    price: float
    tax: Optional[float] = None


item_examples = {
    "With tax": Item(name="foo", price=1, tax=1),
    "Duty Free": Item(name="foo", price=2, tax=0),
}


async def create_receipt(
    item: Annotated[Item, Json(examples=item_examples)]
) -> Dict[str, float]:
    return {item.name: item.price + (item.tax or 0)}


app = App(
    routes=[
        Path(
            "/items/",
            post=create_receipt,
        )
    ]
)
