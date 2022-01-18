import inspect
import typing
from dataclasses import dataclass, field

from pydantic.fields import ModelField

from xpresso._openapi_providers.api import OpenAPIParameter, OpenAPIParameterMarker
from xpresso._openapi_providers.utils import parse_examples
from xpresso._utils.typing import model_field_from_param
from xpresso.openapi import models as openapi_models

Examples = typing.Optional[typing.Mapping[str, openapi_models.Example]]


@dataclass(frozen=True)
class OpenAPIParameterBase(OpenAPIParameter):
    name: str
    in_: str
    required: bool
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    examples: Examples = field(compare=False)
    field: ModelField = field(compare=False)


@dataclass(frozen=True)
class OpenAPIParameterMarkerBase(OpenAPIParameterMarker):
    alias: typing.Optional[str]
    in_: str
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    examples: Examples
    cls: typing.ClassVar[typing.Type[OpenAPIParameterBase]]

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIParameterBase:
        field = model_field_from_param(param)
        name = self.alias or field.alias
        return self.cls(
            name=name,
            in_=self.in_,
            required=field.required is not False,
            field=field,
            style=self.style,
            explode=self.explode,
            description=self.description,
            deprecated=self.deprecated,
            examples=parse_examples(self.examples) if self.examples else None,
        )
