import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import Request

from xpresso._utils.typing import Some, model_field_from_param
from xpresso.binders._body.extractors.body_field_validation import validate_body_field
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._utils.stream_to_bytes import convert_stream_to_bytes
from xpresso.binders.api import BodyExtractor
from xpresso.exceptions import RequestValidationError


class FileBodyExtractor:
    __slots__ = ("field", "media_type_validator", "consume")

    def __init__(
        self,
        field: ModelField,
        media_type_validator: MediaTypeValidator,
        consume: bool,
    ) -> None:
        self.field = field
        self.media_type_validator = media_type_validator
        self.consume = consume

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract_from_request(self, request: Request) -> typing.Any:
        media_type = request.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        if self.field.type_ is bytes:
            if self.consume:
                data = await convert_stream_to_bytes(request.stream())
                if data is None:
                    return validate_body_field(
                        Some(b""), field=self.field, loc=("body",)
                    )
            else:
                data = await request.body()
            return validate_body_field(Some(data), field=self.field, loc=("body",))
        # create an UploadFile from the body's stream
        file: UploadFile = self.field.type_(  # use the field type to allow users to subclass UploadFile
            filename="body", content_type=media_type or "*/*"
        )
        non_empty_chunks = 0
        chunks = 0
        async for chunk in request.stream():
            non_empty_chunks += len(chunk) != 0
            chunks += 1
            await file.write(chunk)
        await file.seek(0)
        return file

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        return await self._extract(field, loc=loc)

    async def _extract(
        self,
        value: typing.Union[str, UploadFile],
        loc: typing.Iterable[typing.Union[int, str]],
    ) -> typing.Union[bytes, UploadFile]:
        if isinstance(value, str):
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=TypeError("Expected a file, got a string"),
                        loc=tuple(loc),
                    )
                ]
            )
        if self.field.type_ is bytes:
            # user requested bytes
            return await value.read()  # type: ignore  # UploadFile always returns bytes
        return value


class FileBodyExtractorMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        field = model_field_from_param(param)
        if self.media_type and self.enforce_media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        return FileBodyExtractor(
            field=field,
            media_type_validator=media_type_validator,
            consume=self.consume,
        )
