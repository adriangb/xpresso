from collections import defaultdict
from typing import DefaultDict, List

from xpresso import App, Json, Path
from xpresso.typing import Annotated

fake_db: DefaultDict[str, List[str]] = defaultdict(list)


async def add_tags(
    id: str,
    tags: Annotated[
        List[str],
        Json(examples={"Two tags": ["tag1", "tag2"]}),
    ],
) -> None:
    fake_db[id].extend(tags)


async def get_tags(id: str) -> List[str]:
    return fake_db[id]


app = App(
    routes=[
        Path(
            path="/items/{id}/tags",
            post=add_tags,
            get=get_tags,
        ),
    ],
)
