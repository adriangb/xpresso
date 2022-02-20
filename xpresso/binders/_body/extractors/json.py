import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.datastructures import UploadFile
from starlette.requests import Request

from xpresso._utils.compat import Protocol
from xpresso._utils.typing import Some, model_field_from_param
from xpresso.binders._body.extractors.body_field_validation import validate_body_field
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._utils.stream_to_bytes import convert_stream_to_bytes
from xpresso.binders.api import BodyExtractor
from xpresso.exceptions import RequestValidationError


class Decoder(Protocol):
    def __call__(self, s: typing.Union[str, bytes]) -> typing.Any:
        ...


class JsonBodyExtractor:
    __slots__ = ("field", "decoder", "media_type_validator", "consume")

    def __init__(
        self,
        field: ModelField,
        decoder: Decoder,
        media_type_validator: MediaTypeValidator,
        consume: bool,
    ) -> None:
        self.field = field
        self.decoder = decoder
        self.media_type_validator = media_type_validator
        self.consume = consume

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract_from_request(self, request: Request) -> typing.Any:
        loc = ("body",)
        self.media_type_validator.validate(
            request.headers.get("content-type", None), loc=loc
        )
        if self.consume:
            data_from_stream = await convert_stream_to_bytes(request.stream())
            if data_from_stream is None:
                return validate_body_field(None, field=self.field, loc=loc)
        else:
            data_from_stream = await request.body()
        return validate_body_field(
            Some(self._decode(data_from_stream, loc=loc)),
            field=self.field,
            loc=loc,
        )

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        if isinstance(field, UploadFile):
            return self._decode(await field.read(), loc=loc)
        return self._decode(field, loc=loc)

    def _decode(
        self,
        value: typing.Union[str, bytes],
        loc: typing.Iterable[typing.Union[int, str]],
    ) -> typing.Union[bytes, UploadFile]:
        try:
            decoded = self.decoder(value)
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


class JsonBodyExtractorMarker(typing.NamedTuple):
    decoder: Decoder
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        if self.enforce_media_type:
            media_type_validator = get_media_type_validator("application/json")
        else:
            media_type_validator = get_media_type_validator(None)
        return JsonBodyExtractor(
            field=model_field_from_param(param),
            decoder=self.decoder,
            media_type_validator=media_type_validator,
            consume=self.consume,
        )
