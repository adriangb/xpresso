from typing import Any, Callable, Iterable, Type

from starlette.datastructures import UploadFile as StarletteUploadFile


class UploadFile(StarletteUploadFile):
    @classmethod
    def __get_validators__(cls: Type["UploadFile"]) -> Iterable[Callable[..., Any]]:
        return iter([])
