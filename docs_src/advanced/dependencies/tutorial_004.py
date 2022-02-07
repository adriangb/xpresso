from typing import Generator, List

from xpresso import (
    App,
    Depends,
    FromPath,
    HTTPException,
    Path,
    Request,
)
from xpresso.responses import get_response


class StatusCodeLogFile(List[int]):
    pass


def log_response_status_code(
    request: Request,
    log: StatusCodeLogFile,
) -> Generator[None, None, None]:
    try:
        yield
    except HTTPException as exc:
        log.append(exc.status_code)
        raise
    else:
        response = get_response(request)
        log.append(response.status_code)


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
            dependencies=[
                Depends(log_response_status_code, scope="connection")
            ],
        ),
    ]
)
