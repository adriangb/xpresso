import inspect
import typing

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field
from starlette.datastructures import FormData, UploadFile
from starlette.requests import HTTPConnection, Request

import xpresso.openapi.models as openapi_models
from xpresso._utils.pydantic_utils import is_sequence_like, model_field_from_param
from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import get_args, get_type_hints
from xpresso.binders._binders.formencoded_parsing import Extractor as FormDataExtractor
from xpresso.binders._binders.formencoded_parsing import (
    InvalidSerialization,
    get_extractor,
)
from xpresso.binders._binders.media_type_validator import MediaTypeValidator
from xpresso.binders._binders.pydantic_validators import validate_body_field
from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIMetadata,
    SupportsExtractor,
    SupportsOpenAPI,
)
from xpresso.exceptions import RequestValidationError
from xpresso.openapi._utils import parse_examples
from xpresso.typing import Some


class FormFieldExtractor(typing.NamedTuple):
    style: str
    explode: bool
    field_name: str
    extractor: FormDataExtractor

    async def extract(self, form: FormData) -> typing.Optional[Some]:
        params = [(k, v) for k, v in form.multi_items() if isinstance(v, str)]  # type: ignore
        try:
            return self.extractor(name=self.field_name, params=params)
        except InvalidSerialization as e:
            raise RequestValidationError(
                [
                    ErrorWrapper(
                        exc=TypeError("Data is not a valid URL encoded form"),
                        loc=tuple(("body", self.field_name)),
                    )
                ]
            ) from e


class FormFieldExtractorMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> FormFieldExtractor:
        field = model_field_from_param(param, alias=self.alias)
        extractor = get_extractor(style=self.style, explode=self.explode, field=field)
        return FormFieldExtractor(
            style=self.style,
            explode=self.explode,
            field_name=field.name,
            extractor=extractor,
        )


class FormFieldOpenAPIMetadata(typing.NamedTuple):
    schema: openapi_models.Schema
    encoding: openapi_models.Encoding


class FormFieldOpenAPI(typing.NamedTuple):
    field_name: str
    style: str
    explode: bool
    field: ModelField

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, set()))

    def get_field_openapi(
        self, model_name_map: ModelNameMap, schemas: typing.Dict[str, typing.Any]
    ) -> FormFieldOpenAPIMetadata:
        field_schema = openapi_schema_from_pydantic_field(
            self.field, model_name_map, schemas
        )
        return FormFieldOpenAPIMetadata(
            schema=field_schema,
            encoding=openapi_models.Encoding(
                contentType=None,
                style=self.style,
                explode=self.explode,
            ),
        )


class FormFieldOpenAPIMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> FormFieldOpenAPI:
        field = model_field_from_param(param, alias=self.alias)
        return FormFieldOpenAPI(
            field_name=field.name,
            style=self.style,
            explode=self.explode,
            field=field,
        )


def ensure_field_is_a_file(
    field: typing.Union[str, UploadFile], field_name: str
) -> UploadFile:
    if isinstance(field, str):
        raise RequestValidationError(
            [
                ErrorWrapper(
                    exc=TypeError("Expected a file, got a string"),
                    loc=("body", field_name),
                )
            ]
        )
    return field


class FormFileExtractor(typing.NamedTuple):
    consumer: typing.Callable[[UploadFile], typing.Awaitable[typing.Any]]
    repeated: bool
    field_name: str

    async def extract(
        self,
        form: FormData,
    ) -> typing.Optional[Some]:
        if self.repeated:
            files: "typing.List[typing.Union[bytes, UploadFile]]" = []
            for field_name, field_value in form.multi_items():
                if field_name == self.field_name:
                    file = ensure_field_is_a_file(field_value, field_name)
                    files.append(await self.consumer(file))
            return Some(files)
        if self.field_name not in form:
            return None
        file = ensure_field_is_a_file(form[self.field_name], self.field_name)
        return Some(await self.consumer(file))


class FormFileExtractorMarker(typing.NamedTuple):
    alias: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> FormFileExtractor:
        field = model_field_from_param(param)
        repeated = is_sequence_like(field)
        if field.type_ is bytes:

            async def read_uploadfile_to_bytes(file: UploadFile) -> bytes:
                return await file.read()  # type: ignore[return-value]

            return FormFileExtractor(
                read_uploadfile_to_bytes,
                field_name=self.alias or param.name,
                repeated=repeated,
            )
        elif inspect.isclass(field.type_) and issubclass(field.type_, UploadFile):

            async def read_uploadfile_to_uploadfile(file: UploadFile) -> UploadFile:
                return file

            return FormFileExtractor(
                read_uploadfile_to_uploadfile,
                field_name=self.alias or param.name,
                repeated=repeated,
            )
        else:
            raise TypeError(f"Unknown file type {field.type_.__name__}")


class FormFileOpenAPI(typing.NamedTuple):
    media_type: typing.Optional[str]
    format: str
    nullable: bool
    repeated: bool
    field_name: str

    def get_models(self) -> typing.List[type]:
        return []

    def get_field_openapi(
        self, model_name_map: ModelNameMap, schemas: typing.Dict[str, typing.Any]
    ) -> FormFieldOpenAPIMetadata:
        schema = openapi_models.Schema(
            type="string", format=self.format, nullable=self.nullable or None
        )
        if self.repeated:
            schema = openapi_models.Schema(type="array", items=schema)
        return FormFieldOpenAPIMetadata(
            schema=schema,
            encoding=openapi_models.Encoding(contentType=self.media_type),
        )


class FormFileOpenAPIMarker(typing.NamedTuple):
    media_type: typing.Optional[str]
    format: str
    alias: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> FormFileOpenAPI:
        return FormFileOpenAPI(
            field_name=self.alias or param.name,
            media_type=self.media_type,
            format=self.format,
            nullable=model_field_from_param(param).allow_none,
            repeated=is_sequence_like(model_field_from_param(param)),
        )


class FormFieldMarker(typing.NamedTuple):
    extractor_marker: typing.Union[FormFieldExtractorMarker, FormFileExtractorMarker]
    openapi_marker: typing.Union[FormFieldOpenAPIMarker, FormFileOpenAPIMarker]


class Extractor(typing.NamedTuple):
    field: ModelField
    field_extractors: typing.Mapping[
        str, typing.Union[FormFileExtractor, FormFieldExtractor]
    ]
    media_type_validator: MediaTypeValidator

    def __hash__(self) -> int:
        return hash("form")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        content_type = connection.headers.get("content-type", None)
        if (
            content_type is None
            and connection.headers.get("content-length", "0") == "0"
        ):
            return validate_body_field(None, field=self.field, loc=("body",))
        self.media_type_validator.validate(content_type)
        form = await connection.form()
        res: typing.Dict[str, typing.Any] = {}
        for param_name, extractor in self.field_extractors.items():
            extracted = await extractor.extract(form)
            if isinstance(extracted, Some):
                res[param_name] = extracted.value
        return validate_body_field(
            Some(res),
            field=self.field,
            loc=("body",),
        )


class ExtractorMarker(typing.NamedTuple):
    media_type: str

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        form_data_field = model_field_from_param(param)
        field_extractors: typing.Dict[
            str, typing.Union[FormFileExtractor, FormFieldExtractor]
        ] = {}
        # use pydantic to get rid of outer annotated, optional, etc.
        model = form_data_field.type_
        # workaround https://github.com/samuelcolvin/pydantic/pull/3413
        # by using get_type_hints
        type_hints = get_type_hints(model, include_extras=True)
        for field_param in inspect.signature(model).parameters.values():
            field_param = field_param.replace(annotation=type_hints[field_param.name])
            for m in get_args(field_param.annotation):
                if isinstance(m, (FormFieldMarker)):
                    field_extractor = m.extractor_marker.register_parameter(field_param)
                    break
            else:
                field_extractor = FormFieldExtractorMarker(
                    alias=None, style="form", explode=False
                ).register_parameter(field_param)
            field_extractors[field_param.name] = field_extractor
        return Extractor(
            media_type_validator=MediaTypeValidator(self.media_type),
            field_extractors=field_extractors,
            field=form_data_field,
        )


class OpenAPI(typing.NamedTuple):
    field_openapi_providers: typing.Mapping[
        str, typing.Union[FormFieldOpenAPI, FormFileOpenAPI]
    ]
    required_fields: typing.List[str]
    description: typing.Optional[str]
    examples: typing.Optional[openapi_models.Examples]
    media_type: str
    required: bool
    nullable: bool
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return [
            model
            for provider in self.field_openapi_providers.values()
            for model in provider.get_models()
        ]

    def get_openapi(
        self,
        model_name_map: ModelNameMap,
    ) -> OpenAPIMetadata:
        if not self.include_in_schema:
            return OpenAPIMetadata()
        schemas: typing.Dict[str, typing.Any] = {}
        providers_openapis = {
            field_name: field_openapi.get_field_openapi(
                model_name_map=model_name_map,
                schemas=schemas,
            )
            for field_name, field_openapi in self.field_openapi_providers.items()
        }
        properties = {
            field_name: openapi_meta.schema
            for field_name, openapi_meta in providers_openapis.items()
        }
        encodings = {
            field_name: openapi_meta.encoding
            for field_name, openapi_meta in providers_openapis.items()
        }
        schema = openapi_models.Schema(
            type="object",
            properties=properties,
            required=self.required_fields or None,
            nullable=self.nullable or None,
        )
        media_type = openapi_models.MediaType(
            schema=schema,  # type: ignore
            examples=self.examples,
            encoding=encodings or None,
        )
        return OpenAPIMetadata(
            body=openapi_models.RequestBody(
                content={self.media_type: media_type},
                required=self.required,
            ),
            schemas=schemas,
        )


class OpenAPIMarker(typing.NamedTuple):
    description: typing.Optional[str]
    examples: typing.Optional[
        typing.Dict[str, typing.Union[openapi_models.Example, typing.Any]]
    ]
    media_type: str
    include_in_schema: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPI:
        form_data_field = model_field_from_param(param)
        required = form_data_field.required is not False
        field_openapi_providers: typing.Dict[
            str, typing.Union[FormFieldOpenAPI, FormFileOpenAPI]
        ] = {}
        required_fields: typing.List[str] = []
        # use pydantic to get rid of outer annotated, optional, etc.
        model = form_data_field.type_
        for field_param in inspect.signature(model).parameters.values():
            for m in get_args(field_param.annotation):
                if isinstance(m, FormFieldMarker):
                    field_openapi = m.openapi_marker.register_parameter(field_param)
                    break
            else:
                field_openapi = FormFieldOpenAPIMarker(
                    alias=None, style="form", explode=True
                ).register_parameter(field_param)
            field_name = field_openapi.field_name
            field_openapi_providers[field_name] = field_openapi
            field = model_field_from_param(field_param)
            if field.required is not False:
                required_fields.append(field_name)
        examples = parse_examples(self.examples) if self.examples else None
        return OpenAPI(
            field_openapi_providers=field_openapi_providers,
            required_fields=required_fields,
            description=self.description,
            examples=examples,
            media_type=self.media_type,
            required=required,
            nullable=form_data_field.allow_none,
            include_in_schema=self.include_in_schema,
        )
