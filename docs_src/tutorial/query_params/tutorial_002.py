from typing import Dict

from xpresso import App, FromQuery, Path


async def double(input: FromQuery[int]) -> Dict[str, int]:
    return {"result": input * 2}


app = App(
    routes=[
        Path(
            path="/math/double",
            get=double,
        ),
    ]
)
