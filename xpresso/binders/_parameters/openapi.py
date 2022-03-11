import inspect
import typing

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso._utils.typing import is_sequence_like, model_field_from_param
from xpresso.binders._utils.examples import parse_examples
from xpresso.binders.api import ModelNameMap, Schemas
from xpresso.binders.api import SupportsOpenAPIParameter as SupportsOpenAPIParameter
from xpresso.openapi import models as openapi_models

Examples = typing.Optional[typing.Mapping[str, openapi_models.Example]]


class OpenAPIParameter(typing.NamedTuple):
    name: str
    in_: openapi_models.ParameterLocations
    required: bool
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    include_in_schema: bool
    examples: typing.Optional[openapi_models.Examples]
    field: ModelField
    param_cls: typing.Type[openapi_models.ConcreteParameter]

    def get_openapi_parameter(
        self, model_name_map: ModelNameMap, schemas: Schemas
    ) -> openapi_models.ConcreteParameter:
        return self.param_cls(
            description=self.description or self.field.field_info.description,  # type: ignore[arg-type]
            required=None if self.required is False else True,
            deprecated=self.deprecated,
            style=self.style,
            explode=self.explode,
            schema=openapi_schema_from_pydantic_field(  # type: ignore[arg-type]
                self.field, model_name_map, schemas
            ),
            examples=self.examples,
            name=self.name,
        )

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, known_models=set()))


class OpenAPIParameterMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    include_in_schema: bool
    examples: Examples
    param_cls: typing.Type[openapi_models.ConcreteParameter]
    required: bool = False

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPIParameter:
        field = model_field_from_param(param)
        # pydantic doesn't let you access default values on classes
        # so we use it's special field machinery
        in_: openapi_models.ParameterLocations = self.param_cls.__fields__[
            "in_"
        ].default
        name = self.alias or field.alias
        if field.required is False and self.required:
            raise TypeError(
                f"{in_.title()} parameters MUST be required and MUST NOT have default values"
            )
        if self.required:
            required = True
        elif field.required and not is_sequence_like(field):
            required = True
        else:
            required = False
        return OpenAPIParameter(
            param_cls=self.param_cls,
            name=name,
            in_=in_,
            required=required,
            field=field,
            style=self.style,
            explode=self.explode,
            description=self.description,
            deprecated=self.deprecated,
            include_in_schema=self.include_in_schema,
            examples=parse_examples(self.examples) if self.examples else None,
        )
