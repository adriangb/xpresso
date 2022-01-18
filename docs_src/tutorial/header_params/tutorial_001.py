from typing import Dict, Optional

from xpresso import App, FromHeader, Path


async def read_items(
    accept_language: FromHeader[Optional[str]] = None,
) -> Dict[str, Optional[str]]:
    return {"Accept-Language": accept_language}


app = App(
    routes=[
        Path(
            "/items/",
            get=read_items,
        )
    ]
)
