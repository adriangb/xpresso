import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._body.pydantic_field_validator import validate_body_field
from xpresso.binders._utils.stream_to_bytes import convert_stream_to_bytes
from xpresso.binders.api import SupportsBodyExtractor, SupportsFieldExtractor
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


class _FileBodyExtractor(typing.NamedTuple):
    field: ModelField
    media_type_validator: MediaTypeValidator
    consume: bool

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        media_type = connection.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        if self.field.type_ is bytes:
            if self.consume:
                data = await convert_stream_to_bytes(connection.stream())
                if data is None:
                    return validate_body_field(
                        Some(b""), field=self.field, loc=("body",)
                    )
            else:
                data = await connection.body()
            return validate_body_field(Some(data), field=self.field, loc=("body",))
        # create an UploadFile from the body's stream
        file: UploadFile = self.field.type_(  # use the field type to allow users to subclass UploadFile
            filename="body", content_type=media_type or "*/*"
        )
        non_empty_chunks = 0
        chunks = 0
        async for chunk in connection.stream():
            non_empty_chunks += len(chunk) != 0
            chunks += 1
            await file.write(chunk)
        await file.seek(0)
        return file


class _FileFieldExtractor(typing.NamedTuple):
    field: ModelField

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        if isinstance(field, str):
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
            return await field.read()  # type: ignore  # UploadFile always returns bytes
        return field


class BodyExtractorMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsBodyExtractor:
        field = model_field_from_param(param)
        if self.media_type and self.enforce_media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        return _FileBodyExtractor(
            field=field,
            media_type_validator=media_type_validator,
            consume=self.consume,
        )


class FieldExtractorMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsFieldExtractor:
        return _FileFieldExtractor(field=model_field_from_param(param))
