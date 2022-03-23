import inspect
import json
import typing

import xpresso.openapi.models as openapi_models
from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso._utils.typing import Annotated, get_args, get_origin
from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIMetadata,
    SupportsExtractor,
    SupportsOpenAPI,
)
from xpresso.binders.dependants import Binder, BinderMarker
from xpresso.exceptions import HTTPException, RequestValidationError
from xpresso.requests import HTTPConnection, Request


def get_binders_from_union_annotation(param: inspect.Parameter) -> typing.List[Binder]:
    providers: typing.List[Binder] = []
    annotation = param.annotation
    origin = get_origin(annotation)
    assert origin is Annotated  # if we got called, this must be true
    annotation = next(iter(get_args(annotation)))
    origin = get_origin(annotation)
    if origin is not typing.Union:
        raise TypeError("Outermost type must be a Union")
    args = get_args(annotation)
    for arg in args:
        origin = get_origin(arg)
        assert origin is Annotated  # if we got called, this must be true
        marker = next((m for m in get_args(arg) if isinstance(m, BinderMarker)), None)
        if marker is None:
            raise TypeError(f"Type annotation is missing body marker: {arg}")
        providers.append(marker.register_parameter(param.replace(annotation=arg)))
    return providers


class BodyOpenAPI(typing.NamedTuple):
    description: typing.Optional[str]
    required: bool
    providers: typing.List[SupportsOpenAPI]

    def get_models(self) -> typing.List[type]:
        return [model for p in self.providers for model in p.get_models()]

    def get_openapi(self, model_name_map: ModelNameMap) -> OpenAPIMetadata:
        content: typing.Dict[str, openapi_models.MediaType] = {}
        schemas: typing.Dict[str, typing.Any] = {}
        for provider in self.providers:
            meta = provider.get_openapi(model_name_map)
            if meta.body is None:
                raise TypeError()
            for k, v in meta.body.content.items():
                if k in content:
                    raise ValueError(f"Duplicate bodies for media type {k}")
                content[k] = v
            schemas.update(meta.schemas or {})
        body = openapi_models.RequestBody(
            required=self.required, content=content, description=self.description
        )
        return OpenAPIMetadata(body=body, schemas=schemas)


class BodyOpenAPIMarker(typing.NamedTuple):
    description: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPI:
        field = model_field_from_param(param)
        return BodyOpenAPI(
            providers=[b.openapi for b in get_binders_from_union_annotation(param)],
            required=field.required is not False,
            description=self.description,
        )


class Extractor(typing.NamedTuple):
    providers: typing.Tuple[SupportsExtractor, ...]

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        errors: typing.List[typing.Union[HTTPException, RequestValidationError]] = []
        for provider in self.providers:
            try:
                return await provider.extract(connection)
            except (HTTPException, RequestValidationError) as error:
                if error.status_code >= 500:
                    raise error
                errors.append(error)
        status_codes = [e.status_code for e in errors]
        # we want to return as much info as we can to the client
        # but it is possible for extractors to fail with different reasons/status codes
        # for example, we might have a union of bodies where the first one fails because the
        # media type does not match (a 415 most likely) but the second one fails because the
        # deserialized JSON schema did not validate (a 422 most likely)
        # so if they all fail with the same status code, we return that status code to the client
        # otherwise, the best we can do is a generic 400 bad request
        if len(set(status_codes)) == 1:
            status_code = next(iter(status_codes))
        else:
            status_code = 400  # generic bad request
        detail: typing.List[typing.Any] = []
        for err in errors:
            if isinstance(err, RequestValidationError):
                detail.extend(err.errors())
            else:
                detail.append(err.detail)
        raise HTTPException(status_code=status_code, detail=json.dumps(detail))


class ExtractorMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        return Extractor(
            tuple(b.extractor for b in get_binders_from_union_annotation(param))
        )
