from typing import Any, Callable, Iterable, Type

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
