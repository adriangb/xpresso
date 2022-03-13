import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._utils.stream_to_bytes import convert_stream_to_bytes
from xpresso.binders.api import SupportsBodyExtractor, SupportsFieldExtractor
from xpresso.datastructures import BinaryStream, UploadFile
from xpresso.exceptions import RequestValidationError


async def consume_request_into_bytes(request: Request) -> bytes:
    return await convert_stream_to_bytes(request.stream())


async def read_request_into_bytes(request: Request) -> bytes:
    return await request.body()


def create_consume_request_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> typing.Callable[[Request], typing.Awaitable[UploadFile]]:
    async def consume_request_into_uploadfile(request: Request) -> UploadFile:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        async for chunk in request.stream():
            if chunk:
                await file.write(chunk)
        await file.seek(0)
        return file

    return consume_request_into_uploadfile


def create_read_request_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> typing.Callable[[Request], typing.Awaitable[UploadFile]]:
    async def read_request_into_uploadfile(request: Request) -> UploadFile:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        await file.write(await request.body())
        await file.seek(0)
        return file

    return read_request_into_uploadfile


async def consume_request_into_stream(request: Request) -> BinaryStream:
    return BinaryStream(request.stream())


async def read_request_into_stream(request: Request) -> BinaryStream:
    async def body_iterator() -> typing.AsyncIterator[bytes]:
        yield await request.body()

    return BinaryStream(body_iterator())


async def read_uploadfile_to_bytes(file: StarletteUploadFile) -> bytes:
    await file.seek(0)
    return await file.read()  # type: ignore  # UploadFile's type hints are wrong


async def read_uploadfile_to_uploadfile(file: StarletteUploadFile) -> UploadFile:
    return file  # type: ignore  # this is technically wrong, but we can't really work around it


class _FileBodyExtractor(typing.NamedTuple):
    media_type_validator: MediaTypeValidator
    consumer: typing.Callable[[Request], typing.Awaitable[typing.Any]]

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        media_type = connection.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        return await self.consumer(connection)


class _FileFieldExtractor(typing.NamedTuple):
    consumer: typing.Callable[[StarletteUploadFile], typing.Awaitable[typing.Any]]

    async def extract_from_field(
        self,
        field: typing.Union[str, StarletteUploadFile],
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
        return await self.consumer(field)


class BodyExtractorMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsBodyExtractor:
        if self.media_type and self.enforce_media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        consumer: typing.Callable[[Request], typing.Any]
        field = model_field_from_param(param)
        if field.type_ is bytes:
            if self.consume:
                consumer = consume_request_into_bytes
            else:
                consumer = read_request_into_bytes
        elif inspect.isclass(field.type_) and issubclass(field.type_, UploadFile):
            if self.consume:
                consumer = create_consume_request_into_uploadfile(field.type_)
            else:
                consumer = create_read_request_into_uploadfile(field.type_)
        elif field.type_ is BinaryStream:
            # a stream
            if self.consume:
                consumer = consume_request_into_stream
            else:
                consumer = read_request_into_stream
        else:
            raise TypeError
        return _FileBodyExtractor(
            media_type_validator=media_type_validator,
            consumer=consumer,
        )


class FieldExtractorMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsFieldExtractor:
        field = model_field_from_param(param)
        if field.type_ is bytes:
            return _FileFieldExtractor(read_uploadfile_to_bytes)
        elif field.type_ is UploadFile:
            return _FileFieldExtractor(read_uploadfile_to_uploadfile)
        else:
            raise TypeError
