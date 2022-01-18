import inspect
import typing
from dataclasses import dataclass

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request

from xpresso._utils.media_type_validator import MediaTypeValidator
from xpresso._utils.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._extractors.api import BodyExtractor, BodyExtractorMarker
from xpresso.binders._extractors.body.utils import stream_to_bytes
from xpresso.binders._extractors.validator import validate as validate_data
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


@dataclass(frozen=True)
class FileBodyExtractor(BodyExtractor):
    field: ModelField
    media_type_validator: MediaTypeValidator

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract_from_request(self, request: Request) -> typing.Any:
        media_type = request.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        if self.field.type_ is bytes:
            data = await stream_to_bytes(request.stream())
            if data is None:
                return validate_data(Some(b""), field=self.field, loc=("body",))
            return validate_data(Some(data), field=self.field, loc=("body",))
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

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[str, int]]
    ) -> typing.Optional[Some[typing.Any]]:
        raise NotImplementedError

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

    # These are implemented to work around pecularities of hashing bound methods on Python 3.7
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, __o: object) -> bool:
        return self is __o


@dataclass(frozen=True)
class FileBodyExtractorMarker(BodyExtractorMarker):
    media_type: typing.Optional[str]
    enforce_media_type: bool

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        field = model_field_from_param(param)
        if self.media_type and self.enforce_media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        return FileBodyExtractor(
            field=field,
            media_type_validator=media_type_validator,
        )
