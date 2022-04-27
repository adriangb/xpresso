import collections.abc
import enum
import inspect
import typing
from contextlib import asynccontextmanager

from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso._utils.typing import Literal
from xpresso.binders._binders.media_type_validator import MediaTypeValidator
from xpresso.binders._binders.pydantic_validators import validate_body_field
from xpresso.binders._binders.utils import (
    Consumer,
    ConsumerContextManager,
    wrap_consumer_as_cm,
)
from xpresso.binders.api import ModelNameMap, SupportsExtractor, SupportsOpenAPI
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


RequestConsumer = Consumer[Request]
RequestConsumerContextManger = ConsumerContextManager[Request]


async def consume_into_bytes(request: Request) -> bytes:
    res = bytearray()
    async for chunk in request.stream():
        res.extend(chunk)
    return res


async def read_into_bytes(request: Request) -> bytes:
    return await request.body()


def create_consume_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> RequestConsumerContextManger:
    @asynccontextmanager
    async def consume_into_uploadfile(
        request: Request,
    ) -> typing.AsyncIterator[UploadFile]:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        async for chunk in request.stream():
            if chunk:
                await file.write(chunk)
        await file.seek(0)
        try:
            yield file
        finally:
            await file.close()

    return consume_into_uploadfile


def create_read_into_uploadfile(
    cls: typing.Type[UploadFile],
) -> RequestConsumerContextManger:
    @asynccontextmanager
    async def read_into_uploadfile(
        request: Request,
    ) -> typing.AsyncIterator[UploadFile]:
        file = cls(
            filename="body", content_type=request.headers.get("Content-Type", "*/*")
        )
        await file.write(await request.body())
        await file.seek(0)
        try:
            yield file
        finally:
            await file.close()

    return read_into_uploadfile


async def consume_into_stream(request: Request) -> typing.AsyncIterator[bytes]:
    return request.stream()


def has_body(conn: HTTPConnection) -> bool:
    if (
        "transfer-encoding" in conn.headers
        and conn.headers["transfer-encoding"] == "chunked"
    ):
        # when transfer encoding is chunked, the content length header is omitted
        return True
    content_length = conn.headers.get("content-length", None)
    if content_length is not None and content_length != "0":
        return True
    return False


class Extractor(typing.NamedTuple):
    media_type_validator: MediaTypeValidator
    consumer_cm: RequestConsumerContextManger
    field: ModelField

    def __hash__(self) -> int:
        return hash("file")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor)

    async def extract(
        self, connection: HTTPConnection
    ) -> typing.AsyncIterator[typing.Any]:
        assert isinstance(connection, Request)
        if not has_body(connection):
            yield validate_body_field(None, field=self.field, loc=("body",))
            return
        media_type = connection.headers.get("content-type", None)
        self.media_type_validator.validate(media_type)
        async with self.consumer_cm(connection) as res:
            yield res


class ExtractorMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        if self.media_type and self.enforce_media_type:
            media_type_validator = MediaTypeValidator(self.media_type)
        else:
            media_type_validator = MediaTypeValidator(None)
        consumer_cm: RequestConsumerContextManger
        field = model_field_from_param(param, arbitrary_types_allowed=True)
        file_type = get_file_type(field)
        if file_type is FileType.bytes:
            if self.consume:
                consumer_cm = wrap_consumer_as_cm(consume_into_bytes)
            else:
                consumer_cm = wrap_consumer_as_cm(read_into_bytes)
        elif file_type is FileType.uploadfile:
            if self.consume:
                consumer_cm = create_consume_into_uploadfile(field.type_)
            else:
                consumer_cm = create_read_into_uploadfile(field.type_)
        else:  # stream
            if self.consume:
                consumer_cm = wrap_consumer_as_cm(consume_into_stream)
            else:
                raise ValueError("consume=False is not supported for streams")
        return Extractor(
            media_type_validator=media_type_validator,
            consumer_cm=consumer_cm,
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

    def modify_operation_schema(
        self,
        model_name_map: ModelNameMap,
        operation: openapi_models.Operation,
        components: openapi_models.Components,
    ) -> None:
        if not self.include_in_schema:
            return
        operation.requestBody = operation.requestBody or openapi_models.RequestBody(
            content={}
        )
        if not isinstance(
            operation.requestBody, openapi_models.RequestBody
        ):  # pragma: no cover
            raise ValueError(
                "Expected request body to be a RequestBody object, found a reference"
            )
        operation.requestBody.content[self.media_type] = openapi_models.MediaType(
            schema=openapi_models.Schema(  # type: ignore
                type="string",
                format=self.format,
                nullable=self.nullable or None,
            ),
            examples=self.examples,
        )
        operation.requestBody.required = operation.requestBody.required or self.required
        operation.requestBody.description = (
            operation.requestBody.description or self.description
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
