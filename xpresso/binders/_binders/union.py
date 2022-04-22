import inspect
import typing

import xpresso.openapi.models as openapi_models
from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso._utils.typing import Annotated, get_args, get_origin
from xpresso.binders.api import ModelNameMap, SupportsExtractor, SupportsOpenAPI
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

    def modify_operation_schema(
        self,
        model_name_map: ModelNameMap,
        operation: openapi_models.Operation,
        components: openapi_models.Components,
    ) -> None:
        for provider in self.providers:
            provider.modify_operation_schema(model_name_map, operation, components)


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
        errors: "typing.List[typing.Union[HTTPException, RequestValidationError]]" = []
        for provider in self.providers:
            try:
                return await provider.extract(connection)
            except (HTTPException, RequestValidationError) as error:
                errors.append(error)
        # if any body accepted the request but didn't pass validation, return the error from that one
        for err in errors:
            if err.status_code == 422:
                raise err
        # otherwise, just raise the first error we found
        # this is somewhat arbitrary, but there really is no good way to "merge"
        # all of the errors without making it confusing to the client
        # and leaking implementation details
        raise next(iter(errors))


class ExtractorMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        return Extractor(
            tuple(b.extractor for b in get_binders_from_union_annotation(param))
        )
