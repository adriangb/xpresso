import typing


async def stream_to_bytes(
    stream: typing.AsyncGenerator[bytes, None]
) -> typing.Optional[bytes]:
    data: typing.List[bytes] = []
    async for chunk in stream:  # pragma: no cover # stream always has at least 1 chunk
        data.append(chunk)
    if len(data) == 1 and data[0] == b"":
        # no content received
        return None
    return b"".join(data)
