import fnmatch
import functools
import re
import typing

from pydantic.error_wrappers import ErrorWrapper
from starlette import status

from xpresso.exceptions import RequestValidationError


class MediaTypeValidator:
    __slots__ = ("accepted",)

    def __init__(self, media_type: typing.Optional[str]) -> None:
        if media_type is None:
            self.accepted = None
        else:
            self.accepted = [
                re.compile(fnmatch.translate(p)) for p in media_type.lower().split(",")
            ]

    def matches(self, media_type: typing.Optional[str]) -> bool:
        if self.accepted is None:
            return True
        if media_type is None:
            return False
        media_type = next(iter(media_type.split(";"))).lower()
        return any(accepted.match(media_type) for accepted in self.accepted)

    def validate(
        self,
        media_type: typing.Optional[str],
        loc: typing.Tuple[typing.Union[int, str], ...],
    ) -> None:
        if self.accepted is None:
            return
        if media_type is None:
            raise RequestValidationError(
                errors=[
                    ErrorWrapper(
                        ValueError("Media type missing in content-type header"),
                        loc=tuple((*loc, "headers", "content-type")),
                    )
                ],
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        media_type = next(iter(media_type.split(";"))).lower()
        for accepted in self.accepted:
            if accepted.match(media_type):
                return
        raise RequestValidationError(
            errors=[
                ErrorWrapper(
                    ValueError(f"Media type {media_type} is not supported"),
                    loc=tuple((*loc, "headers", "content-type")),
                )
            ],
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


@functools.lru_cache(maxsize=1024)
def get_validator(media_type: typing.Optional[str]) -> MediaTypeValidator:
    return MediaTypeValidator(media_type)
