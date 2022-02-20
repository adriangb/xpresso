import inspect
import typing

from di.typing import get_markers_from_parameter

from xpresso._utils.compat import Annotated, get_args, get_origin
from xpresso._utils.typing import model_field_from_param
from xpresso.binders.api import ModelNameMap, OpenAPIBody, Schemas
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models as openapi_models


class OpenAPIContentTypeDiscriminated(typing.NamedTuple):
    sub_body_providers: typing.Iterable[OpenAPIBody]
    description: typing.Optional[str]
    required: typing.Optional[bool]
    include_in_schema: bool

    def get_models(self) -> typing.List[type]:
        return [model for b in self.sub_body_providers for model in b.get_models()]

    def get_openapi_body(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        content: typing.Dict[str, openapi_models.MediaType] = {}
        for body in self.sub_body_providers:
            content.update(body.get_openapi_body(model_name_map, schemas).content)
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content=content,
        )

    def get_field_encoding(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Encoding:
        raise NotImplementedError

    def get_field_schema(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.Schema:
        raise NotImplementedError


class OpenAPIContentTypeDiscriminatedMarker(typing.NamedTuple):
    description: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        required = field.required is not False
        sub_body_providers: typing.List[OpenAPIBody] = []

        annotation = param.annotation
        origin = get_origin(annotation)
        assert origin is Annotated
        annotation = next(iter(get_args(annotation)))
        origin = get_origin(annotation)
        if origin is not typing.Union:
            raise TypeError("Unioned bodies must be a Union of simple bodies")
        args = get_args(annotation)
        for arg in args:
            sub_body_param = inspect.Parameter(
                name=param.name,
                kind=param.kind,
                annotation=arg,
                default=param.default,
            )
            for param_marker in get_markers_from_parameter(sub_body_param):
                if isinstance(param_marker, BodyBinderMarker):
                    marker = param_marker
                    break
            else:
                raise TypeError(f"Type annotation is missing body marker: {arg}")
            sub_body_openapi = marker.openapi_marker
            provider = sub_body_openapi.register_parameter(sub_body_param)
            if provider.include_in_schema:
                sub_body_providers.append(provider)
        return OpenAPIContentTypeDiscriminated(
            sub_body_providers=sub_body_providers,
            description=self.description,
            required=None if required else False,
            include_in_schema=True,
        )
