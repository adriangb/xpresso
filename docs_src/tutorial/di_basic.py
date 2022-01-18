from typing import Any, Dict, Optional

from xpresso import App, FromQuery, Path
from xpresso.dependencies.models import Dependant
from xpresso.typing import Annotated


async def common_parameters(
    q: FromQuery[Optional[str]] = None,
    skip: FromQuery[int] = 0,
    limit: FromQuery[int] = 100,
):
    return {"q": q, "skip": skip, "limit": limit}


async def read_items(
    commons: Annotated[Dict[str, Any], Dependant(common_parameters)]
) -> Dict[str, Any]:
    return commons


async def read_users(
    commons: Annotated[Dict[str, Any], Dependant(common_parameters)]
) -> Dict[str, Any]:
    return commons


app = App(
    routes=[
        Path(path="/items/", get=read_items),
        Path(path="/users/", get=read_users),
    ]
)
