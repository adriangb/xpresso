from collections import defaultdict
from typing import DefaultDict, List

from xpresso import App, FromJson, Path

fake_db: DefaultDict[str, List[str]] = defaultdict(list)


async def add_tags(
    id: str,
    tags: FromJson[List[str]],
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
