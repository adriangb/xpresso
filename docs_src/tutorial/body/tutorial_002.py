from typing import Dict, Optional

from pydantic import BaseModel, Field

from xpresso import App, FromJson, Path
from xpresso.typing import Annotated


class Item(BaseModel):
    name: str
    price: Annotated[
        float,
        Field(
            gt=0,
            description="Item price without tax. Must be greater than zero.",
        ),
    ]
    tax: Optional[float] = None


async def create_receipt(item: FromJson[Item]) -> Dict[str, float]:
    return {item.name: item.price + (item.tax or 0)}


app = App(
    routes=[
        Path(
            "/items/",
            post=create_receipt,
        )
    ]
)
