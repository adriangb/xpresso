import collections.abc
import enum
import inspect
import typing

from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso._utils.typing import Literal
from xpresso.binders._binders.media_type_validator import MediaTypeValidator
from xpresso.binders._binders.pydantic_validators import validate_body_field
from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIMetadata,
    SupportsExtractor,
    SupportsOpenAPI,
)
from xpresso.openapi import models as openapi_models
from xpresso.openapi._utils import parse_examples


class FileType(enum.Enum):
    bytes = enum.auto()
    uploadfile = enum.auto()
    stream = enum.auto()


STREAM_TYPES = (typing.AsyncIterator, typing.AsyncGenerator, typing.AsyncIterable, collections.abc.AsyncGenerator, collections.abc.AsyncIterable, collections.abc.AsyncIterator)  # type: ignore


def get_file_type(field: ModelField) -> FileType:
    if field.type_ is bytes:
        return FileType.bytes
    if inspect.isclass(field.type_) and issubclass(field.type_, UploadFile):
        return FileType.uploadfile
    if field.type_ in STREAM_TYPES:  # type: ignore
        return FileType.stream
    raise TypeError(f"Target type {field.type_.__name__} is not recognized")


async def consume_into_bytes(request: Request) -> bytes:
    res = bytearray()
    async for chunk in request.stream():
        res.extend(chunk)
    return res


async def read_into_bytes(request: Request) -> bytes:
    return await request.body()


def create_consume_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> typing.Callable[[Request], typing.Awaitable[UploadFile]]:
    async def consume_into_uploadfile(request: Request) -> UploadFile:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        async for chunk in request.stream():
            if chunk:
                await file.write(chunk)
        await file.seek(0)
        return file

    return consume_into_uploadfile


def create_read_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> typing.Callable[[Request], typing.Awaitable[UploadFile]]:
    async def read_into_uploadfile(request: Request) -> UploadFile:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        await file.write(await request.body())
        await file.seek(0)
        return file

    return read_into_uploadfile


async def consume_into_stream(request: Request) -> typing.AsyncIterator[bytes]:
    return request.stream()


class Extractor(typing.NamedTuple):
    media_type_validator: MediaTypeValidator
    consumer: typing.Callable[[Request], typing.Awaitable[typing.Any]]
    field: ModelField

    def __hash__(self) -> int:
        return hash("file")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        media_type = connection.headers.get("content-type", None)
        if media_type is None and connection.headers.get("content-length", "0") == "0":
            return validate_body_field(None, field=self.field, loc=("body",))
        self.media_type_validator.validate(media_type)
        return await self.consumer(connection)


class ExtractorMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        if self.media_type and self.enforce_media_type:
            media_type_validator = MediaTypeValidator(self.media_type)
        else:
            media_type_validator = MediaTypeValidator(None)
        consumer: typing.Callable[[Request], typing.Any]
        field = model_field_from_param(param, arbitrary_types_allowed=True)
        file_type = get_file_type(field)
        if file_type is FileType.bytes:
            if self.consume:
                consumer = consume_into_bytes
            else:
                consumer = read_into_bytes
        elif file_type is FileType.uploadfile:
            if self.consume:
                consumer = create_consume_into_uploadfile(field.type_)
            else:
                consumer = create_read_into_uploadfile(field.type_)
        else:  # stream
            if self.consume:
                consumer = consume_into_stream
            else:
                raise ValueError("consume=False is not supported for streams")
        return Extractor(
            media_type_validator=media_type_validator,
            consumer=consumer,
            field=field,
        )


class OpenAPI(typing.NamedTuple):
    media_type: str
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    format: Literal["binary", "base64"]
    required: bool
    nullable: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return []

    def get_openapi(
        self,
        model_name_map: ModelNameMap,
    ) -> OpenAPIMetadata:
        if not self.include_in_schema:
            return OpenAPIMetadata()
        return OpenAPIMetadata(
            body=openapi_models.RequestBody(
                content={
                    self.media_type: openapi_models.MediaType(
                        schema=openapi_models.Schema(  # type: ignore
                            type="string",
                            format=self.format,
                            nullable=self.nullable or None,
                        ),
                        examples=self.examples,
                    )
                },
                description=self.description,
                required=self.required,
            )
        )


class OpenAPIMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    format: Literal["binary", "base64"]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPI:
        field = model_field_from_param(param, arbitrary_types_allowed=True)
        examples = parse_examples(self.examples) if self.examples else None
        required = field.required is not False
        return OpenAPI(
            media_type=self.media_type or "*/*",
            description=self.description,
            examples=examples,
            format=self.format,
            required=required,
            nullable=field.allow_none,
            include_in_schema=self.include_in_schema,
        )
