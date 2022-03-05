import inspect
from typing import Any, Awaitable, Callable, ClassVar, Dict

from di.typing import get_markers_from_annotation
from pydantic import BaseModel, ValidationError
from starlette.requests import HTTPConnection

from xpresso.binders.dependants import SecurityBinderMarker
from xpresso.exceptions import HTTPException


class SecurityModel(BaseModel):
    _extract: ClassVar[Callable[[HTTPConnection], Awaitable[Any]]]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        extractors: Dict[str, Callable[[HTTPConnection], Awaitable[Any]]] = {}
        for field in cls.__fields__.values():
            marker = next(
                iter(
                    get_markers_from_annotation(field.outer_type_, SecurityBinderMarker)
                ),
                None,
            )
            if marker is None:
                raise TypeError
            param = inspect.Parameter(
                name=field.name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=field.get_default(),
                annotation=field.outer_type_,
            )
            extractors[field.name] = marker.register_parameter(param).call  # type: ignore

        async def extract(conn: HTTPConnection) -> Any:
            try:
                return cls(
                    **{
                        param_name: await extractor(conn)
                        for param_name, extractor in extractors.items()
                    }
                )  # type: ignore
            except ValidationError:
                raise HTTPException(status_code=401, detail="Not authenticated")

        cls._extract = extract

    @classmethod
    async def extract(cls, conn: HTTPConnection) -> Any:
        return await cls._extract(conn)
