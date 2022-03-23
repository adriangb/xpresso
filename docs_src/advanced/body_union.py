from typing import Dict, Optional, Union

from pydantic import BaseModel

from xpresso import App, FromBodyUnion, FromFormData, FromJson, Path


class Item(BaseModel):
    name: str
    price: float
    tax: Optional[float] = None


async def create_receipt(
    item: FromBodyUnion[Union[FromJson[Item], FromFormData[Item]]]
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
