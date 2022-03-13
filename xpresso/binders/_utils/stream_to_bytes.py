import typing


async def convert_stream_to_bytes(stream: typing.AsyncIterator[bytes]) -> bytearray:
    data = bytearray()
    async for chunk in stream:  # pragma: no cover # stream always has at least 1 chunk
        data.extend(chunk)
    return data
