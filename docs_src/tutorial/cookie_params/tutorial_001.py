from typing import Dict, Optional

from xpresso import App, FromCookie, Path


async def read_items(
    advertiser_id: FromCookie[Optional[int]] = None,
) -> Dict[str, Optional[int]]:
    return {"advertiser_id": advertiser_id}


app = App(
    routes=[
        Path(
            "/items/",
            get=read_items,
        )
    ]
)
