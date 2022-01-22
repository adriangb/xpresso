from typing import Generator
from uuid import UUID, uuid4

from xpresso import App, Dependant, FromPath, HTTPException, Path, Request
from xpresso.responses import get_response

CONTEXT_HEADER = "X-Request-Context"


def trace(request: Request) -> Generator[None, None, None]:
    req_ctx = request.headers.get(CONTEXT_HEADER, None)
    if req_ctx is not None:
        ctx = UUID(req_ctx)
    else:
        ctx = uuid4()
    try:
        yield
    except HTTPException as exc:
        exc.headers[CONTEXT_HEADER] = str(ctx)
        raise
    else:
        response = get_response(request)
        response.headers[CONTEXT_HEADER] = str(ctx)


fake_items_db = {"foo": "Foo", "bar": "Bar"}


async def read_items(item_name: FromPath[str]) -> str:
    if item_name in fake_items_db:
        return fake_items_db[item_name]
    raise HTTPException(status_code=404)


app = App(
    routes=[
        Path(
            path="/items/{item_name}",
            get=read_items,
            dependencies=[Dependant(trace)],
        ),
    ]
)
