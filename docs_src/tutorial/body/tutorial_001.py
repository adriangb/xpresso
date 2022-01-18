from typing import Dict, Optional

from pydantic import BaseModel

from xpresso import App, FromJson, Path


class Item(BaseModel):
    name: str
    price: float
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
