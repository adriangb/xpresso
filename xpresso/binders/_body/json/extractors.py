import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.compat import Protocol
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


class SupportsJsonDecoder(Protocol):
    def __call__(self, s: typing.Union[str, bytes]) -> typing.Any:
        ...


def _decode(
    decoder: SupportsJsonDecoder,
    value: typing.Union[str, bytes],
    loc: typing.Iterable[typing.Union[int, str]],
) -> typing.Union[bytes, UploadFile]:
    try:
        decoded = decoder(value)
    except Exception as e:
        raise RequestValidationError(
            [
                ErrorWrapper(
                    exc=TypeError("Data is not valid JSON"),
                    loc=tuple(loc),
                )
            ]
        ) from e
    return decoded


class _BodyExtractor(typing.NamedTuple):
    field: ModelField
    decoder: SupportsJsonDecoder
    media_type_validator: MediaTypeValidator
    consume: bool

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        loc = ("body",)
        self.media_type_validator.validate(
            connection.headers.get("content-type", None), loc=loc
        )
        if self.consume:
            data_from_stream = await convert_stream_to_bytes(connection.stream())
            if data_from_stream is None:
                return validate_body_field(None, field=self.field, loc=loc)
        else:
            data_from_stream = await connection.body()
        return validate_body_field(
            Some(_decode(self.decoder, data_from_stream, loc=loc)),
            field=self.field,
            loc=loc,
        )


class _FieldExtractor(typing.NamedTuple):
    decoder: SupportsJsonDecoder

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        if isinstance(field, UploadFile):
            return _decode(self.decoder, await field.read(), loc=loc)
        return _decode(self.decoder, field, loc=loc)


class BodyExtractorMarker(typing.NamedTuple):
    decoder: SupportsJsonDecoder
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsBodyExtractor:
        if self.enforce_media_type:
            media_type_validator = get_media_type_validator("application/json")
        else:
            media_type_validator = get_media_type_validator(None)
        return _BodyExtractor(
            field=model_field_from_param(param),
            decoder=self.decoder,
            media_type_validator=media_type_validator,
            consume=self.consume,
        )


class FieldExtractorMarker(typing.NamedTuple):
    decoder: SupportsJsonDecoder

    def register_parameter(self, param: inspect.Parameter) -> SupportsFieldExtractor:
        return _FieldExtractor(self.decoder)
