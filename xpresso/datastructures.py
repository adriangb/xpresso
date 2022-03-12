from typing import Any, AsyncIterator, Callable, Iterable, Type

from starlette.datastructures import UploadFile as StarletteUploadFile


class UploadFile(StarletteUploadFile):
    @classmethod
    def __get_validators__(cls: Type["UploadFile"]) -> Iterable[Callable[..., Any]]:
        return iter(())


class BinaryStream(AsyncIterator[bytes]):
    def __init__(self, stream: AsyncIterator[bytes]) -> None:
        self._stream = stream

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._stream.__aiter__()

    async def __anext__(self) -> bytes:
        return await self._stream.__anext__()

    @classmethod
    def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
        return iter(())
