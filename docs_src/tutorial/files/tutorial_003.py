from typing import AsyncIterator

from xpresso import App, FromFile, Path


async def count_bytes_in_file(
    data: FromFile[AsyncIterator[bytes]],
) -> int:
    size = 0
    async for chunk in data:
        size += len(chunk)
    return size


app = App(routes=[Path(path="/count-bytes", put=count_bytes_in_file)])
