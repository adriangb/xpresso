import inspect
import typing

from pydantic.fields import ModelField
from pydantic.schema import get_flat_models_from_field

from xpresso._utils.pydantic_utils import is_sequence_like, model_field_from_param
from xpresso._utils.schemas import openapi_schema_from_pydantic_field
from xpresso.binders.api import ModelNameMap, OpenAPIMetadata, SupportsOpenAPI
from xpresso.openapi import models as openapi_models
from xpresso.openapi._utils import parse_examples

Examples = typing.Optional[typing.Mapping[str, openapi_models.Example]]


class OpenAPI(typing.NamedTuple):
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

    def get_openapi(self, model_name_map: ModelNameMap) -> OpenAPIMetadata:
        if not self.include_in_schema:
            return OpenAPIMetadata()
        schemas: typing.Dict[str, typing.Any] = {}
        schema = openapi_schema_from_pydantic_field(  # type: ignore[arg-type]
            self.field, model_name_map, schemas
        )
        return OpenAPIMetadata(
            parameters=[
                self.param_cls(
                    description=self.description or self.field.field_info.description,
                    required=None if self.required is False else True,
                    deprecated=self.deprecated,
                    style=self.style,
                    explode=self.explode,
                    schema=schema,  # type: ignore[arg-type]
                    examples=self.examples,
                    name=self.name,
                )
            ],
            schemas=schemas,
        )

    def get_models(self) -> typing.List[type]:
        return list(get_flat_models_from_field(self.field, known_models=set()))


class OpenAPIMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    style: str
    explode: bool
    description: typing.Optional[str]
    deprecated: typing.Optional[bool]
    include_in_schema: bool
    examples: Examples
    param_cls: typing.Type[openapi_models.ConcreteParameter]
    required: bool = False

    def register_parameter(self, param: inspect.Parameter) -> SupportsOpenAPI:
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
        return OpenAPI(
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
