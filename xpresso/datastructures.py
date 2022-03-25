from typing import Any, AsyncIterator, Callable, Iterable, Type

from starlette.datastructures import UploadFile as StarletteUploadFile


class UploadFile(StarletteUploadFile):
    @classmethod
    def __get_validators__(cls: Type["UploadFile"]) -> Iterable[Callable[..., Any]]:
        # this is required so that UploadFile can be a Pydantic field
        return iter(())

    async def read(self, size: int = -1) -> bytes:
        # this is implemented just to fix the return type annotation
        # which is always bytes
        return await super().read(size)  # type: ignore


class BinaryStream(AsyncIterator[bytes]):
    def __init__(self, stream: AsyncIterator[bytes]) -> None:
        self._stream = stream

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._stream.__aiter__()

    async def __anext__(self) -> bytes:  # pragma: no cover
        return await self._stream.__anext__()

    @classmethod
    def __get_validators__(cls) -> Iterable[Callable[..., Any]]:
        # this is required so that this class can be a Pydantic field
        return iter(())
