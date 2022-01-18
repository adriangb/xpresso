from typing import Optional

from pydantic import BaseModel

from xpresso import App, FromQuery, Path


class Filter(BaseModel):
    prefix: str
    limit: int
    skip: int = 0


async def read_items(filter: FromQuery[Optional[Filter]]) -> Optional[Filter]:
    return filter


app = App(
    routes=[
        Path(
            path="/items/",
            get=read_items,
        ),
    ]
)
