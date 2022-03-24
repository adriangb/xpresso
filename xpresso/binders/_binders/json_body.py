import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field
from starlette.datastructures import UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import Protocol
from xpresso.binders._binders.media_type_validator import MediaTypeValidator
from xpresso.binders._binders.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._binders.pydantic_validators import validate_body_field
from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIMetadata,
    SupportsExtractor,
    SupportsOpenAPI,
)
from xpresso.exceptions import RequestValidationError
from xpresso.openapi import models as openapi_models
from xpresso.openapi._utils import parse_examples
from xpresso.typing import Some


class SupportsJsonDecoder(Protocol):
    def __call__(self, s: typing.Union[str, bytes]) -> typing.Any:
        ...


def _decode(
    decoder: SupportsJsonDecoder,
    value: typing.Union[str, bytes],
) -> typing.Union[bytes, UploadFile]:
    try:
        decoded = decoder(value)
    except Exception as e:
        raise RequestValidationError(
            [
                ErrorWrapper(
                    exc=TypeError("Data is not valid JSON"),
                    loc=("body",),
                )
            ]
        ) from e
    return decoded


class Extractor(typing.NamedTuple):
    field: ModelField
    decoder: SupportsJsonDecoder
    media_type_validator: MediaTypeValidator
    consume: bool

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        loc = ("body",)
        self.media_type_validator.validate(connection.headers.get("content-type", None))
        data_from_stream: bytes
        if self.consume:
            data_from_stream = bytearray()
            async for chunk in connection.stream():
                data_from_stream.extend(chunk)
        else:
            data_from_stream = await connection.body()
        if len(data_from_stream) == 0:
            return validate_body_field(
                None,
                field=self.field,
                loc=loc,
            )
        return validate_body_field(
            Some(_decode(self.decoder, data_from_stream)),
            field=self.field,
            loc=loc,
        )


class ExtractorMarker(typing.NamedTuple):
    decoder: SupportsJsonDecoder
    enforce_media_type: bool
    consume: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        if self.enforce_media_type:
            media_type_validator = get_media_type_validator("application/json")
        else:
            media_type_validator = get_media_type_validator(None)
        return Extractor(
            field=model_field_from_param(param),
            decoder=self.decoder,
            media_type_validator=media_type_validator,
            consume=self.consume,
        )


class OpenAPI(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    field: ModelField
    required: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_openapi(self, model_name_map: ModelNameMap) -> OpenAPIMetadata:
        if not self.include_in_schema:
            return OpenAPIMetadata()
        schemas: typing.Dict[str, typing.Any] = {}
        content = {
            "application/json": openapi_models.MediaType(
                schema=openapi_schema_from_pydantic_field(  # type: ignore
                    self.field, model_name_map, schemas
                ),
                examples=self.examples,
            )
        }
        body = openapi_models.RequestBody(required=self.required, content=content)
        return OpenAPIMetadata(body=body, schemas=schemas)


class OpenAPIMarker(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPI:
        examples = parse_examples(self.examples) if self.examples else None
        field = model_field_from_param(param)
        required = field.required is not False
        return OpenAPI(
            description=self.description,
            examples=examples,
            field=field,
            required=required,
            include_in_schema=self.include_in_schema,
        )
