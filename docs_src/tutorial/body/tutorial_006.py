import json
from typing import Any, Dict

from pydantic import BaseModel

from xpresso import App, Json, Path, RawBody
from xpresso.typing import Annotated


class WebhookBody(BaseModel):
    name: str


async def handle_event(
    event: Annotated[Dict[str, Any], Json(consume=False)],
    raw_body: Annotated[bytes, RawBody(consume=False)],
) -> bool:
    return json.loads(raw_body) == event


app = App(
    routes=[
        Path(
            "/webhook",
            post=handle_event,
        )
    ]
)
