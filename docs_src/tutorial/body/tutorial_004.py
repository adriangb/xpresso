from typing import Dict, List, Optional

from pydantic import BaseModel

from xpresso import App, FromJson, Path


class Item(BaseModel):
    name: str
    price: float
    tax: Optional[float] = None


async def create_receipt(items: FromJson[List[Item]]) -> Dict[str, float]:
    return {item.name: item.price + (item.tax or 0) for item in items}


app = App(
    routes=[
        Path(
            "/items/",
            post=create_receipt,
        )
    ]
)
