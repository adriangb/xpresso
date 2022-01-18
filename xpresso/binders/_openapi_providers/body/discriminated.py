import inspect
import sys
import typing
from dataclasses import dataclass

if sys.version_info < (3, 9):
    from typing_extensions import Annotated, get_args, get_origin
else:
    from typing import Annotated, get_origin, get_args

from di.typing import get_markers_from_parameter

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    ModelNameMap,
    OpenAPIBody,
    OpenAPIBodyMarker,
    Schemas,
)
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.openapi import models as openapi_models


@dataclass(frozen=True)
class OpenAPIContentTypeDiscriminated(OpenAPIBody):
    sub_body_providers: typing.Mapping[str, OpenAPIBody]
    description: typing.Optional[str]
    required: typing.Optional[bool]

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.RequestBody:
        return openapi_models.RequestBody(
            description=self.description,
            required=self.required,
            content={
                media_type: provider.get_media_type_object(model_name_map, schemas)
                for media_type, provider in self.sub_body_providers.items()
            },
        )


@dataclass(frozen=True)
class OpenAPIContentTypeDiscriminatedMarker(OpenAPIBodyMarker):
    description: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIBody:
        field = model_field_from_param(param)
        if field.required is False:
            required = False
        else:
            required = True

        sub_body_providers: typing.Dict[str, OpenAPIBody] = {}

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
            marker: typing.Optional[BodyBinderMarker] = None
            for param_marker in get_markers_from_parameter(sub_body_param):
                if isinstance(param_marker, BodyBinderMarker):
                    marker = param_marker
                    break
            if marker is None:
                raise TypeError(f"Type annotation is missing body marker: {arg}")
            sub_body_openapi = marker.openapi_marker
            provider = sub_body_openapi.register_parameter(sub_body_param)
            media_type = provider.get_media_type()
            sub_body_providers[media_type] = provider
        return OpenAPIContentTypeDiscriminated(
            sub_body_providers=sub_body_providers,
            description=self.description,
            required=None if required else False,
        )
