import inspect
import typing
from dataclasses import dataclass, field

from pydantic.fields import (
    SHAPE_FROZENSET,
    SHAPE_ITERABLE,
    SHAPE_LIST,
    SHAPE_SEQUENCE,
    SHAPE_SET,
    SHAPE_TUPLE_ELLIPSIS,
    ModelField,
)

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._openapi_providers.api import (
    OpenAPIParameter,
    OpenAPIParameterMarker,
)
from xpresso.binders._openapi_providers.utils import parse_examples
from xpresso.openapi import models as openapi_models

Examples = typing.Optional[typing.Mapping[str, openapi_models.Example]]

SEQUENCE_LIKE_SHAPES = (
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_SEQUENCE,
    SHAPE_ITERABLE,
    SHAPE_TUPLE_ELLIPSIS,
    SHAPE_FROZENSET,
)


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
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    examples: Examples
    in_: typing.ClassVar[str]
    cls: typing.ClassVar[typing.Type[OpenAPIParameterBase]]
    must_be_required: typing.ClassVar[bool] = False

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIParameterBase:
        field = model_field_from_param(param)
        name = self.alias or field.alias
        if field.required is False and self.must_be_required:
            raise TypeError(
                f"{self.in_.title()} parameters MUST be required and MUST NOT have default values"
            )
        return self.cls(
            name=name,
            in_=self.in_,
            required=(field.required is not False)
            and (field.shape not in SEQUENCE_LIKE_SHAPES),
            field=field,
            style=self.style,
            explode=self.explode,
            description=self.description,
            deprecated=self.deprecated,
            examples=parse_examples(self.examples) if self.examples else None,
        )
