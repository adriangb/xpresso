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
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import is_sequence_like, model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import (
    ModelNameMap,
    OpenAPIParameter,
    OpenAPIParameterMarker,
    Schemas,
)
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
    include_in_schema: bool
    examples: Examples = field(compare=False)
    field: ModelField = field(compare=False)
    param_cls: typing.ClassVar[typing.Type[openapi_models.ConcreteParameter]]

    def get_openapi(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.ConcreteParameter:
        return self.param_cls(
            description=self.description or self.field.field_info.description,  # type: ignore[arg-type]
            required=None if self.required is False else True,
            deprecated=self.deprecated,
            style=self.style,  # type: ignore[arg-type]
            explode=self.explode,
            schema=openapi_schema_from_pydantic_field(
                self.field, model_name_map, schemas
            ),
            examples=self.examples,  # type: ignore[arg-type]
            name=self.name,
        )

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, known_models=set()))


@dataclass(frozen=True)
class OpenAPIParameterMarkerBase(OpenAPIParameterMarker):
    alias: typing.Optional[str]
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    include_in_schema: bool
    examples: Examples
    in_: typing.ClassVar[str]
    cls: typing.ClassVar[typing.Type[OpenAPIParameterBase]]
    required: typing.ClassVar[bool] = False

    def register_parameter(self, param: inspect.Parameter) -> OpenAPIParameterBase:
        field = model_field_from_param(param)
        name = self.alias or field.alias
        if field.required is False and self.required:
            raise TypeError(
                f"{self.in_.title()} parameters MUST be required and MUST NOT have default values"
            )
        if self.required:
            required = True
        elif field.required and not is_sequence_like(field):
            required = True
        else:
            required = False
        return self.cls(
            name=name,
            in_=self.in_,
            required=required,
            field=field,
            style=self.style,
            explode=self.explode,
            description=self.description,
            deprecated=self.deprecated,
            include_in_schema=self.include_in_schema,
            examples=parse_examples(self.examples) if self.examples else None,
        )
