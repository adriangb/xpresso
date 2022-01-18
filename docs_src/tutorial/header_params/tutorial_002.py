from typing import Dict, Optional

from xpresso import App, HeaderParam, Path
from xpresso.typing import Annotated


async def read_items(
    some_header: Annotated[str, HeaderParam(convert_underscores=False)]
) -> Dict[str, Optional[str]]:
    return {"some_header": some_header}


app = App(
    routes=[
        Path(
            "/items/",
            get=read_items,
        )
    ]
)
