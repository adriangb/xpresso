import inspect
import typing
from enum import Enum

from pydantic import BaseConfig, BaseModel
from pydantic.fields import (
    MAPPING_LIKE_SHAPES,
    SHAPE_FROZENSET,
    SHAPE_LIST,
    SHAPE_SEQUENCE,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
    ModelField,
)
from pydantic.schema import TypeModelOrEnum
from pydantic.schema import get_model_name_map as get_model_name_map_pydantic

from xpresso._utils.compat import Annotated, get_args, get_origin

T = typing.TypeVar("T")


def model_field_from_param(param: inspect.Parameter) -> ModelField:
    return ModelField.infer(
        name=param.name,
        value=param.default if param.default is not param.empty else ...,
        annotation=param.annotation,
        class_validators={},
        config=BaseConfig,
    )


def filter_pydantic_models_from_set(
    s: typing.AbstractSet[typing.Any],
) -> typing.Set[TypeModelOrEnum]:
    def f(x: typing.Any) -> bool:
        return inspect.isclass(x) and issubclass(x, (BaseModel, Enum))

    return set(filter(f, s))


def filter_pydantic_models_from_mapping(
    m: typing.Mapping[typing.Any, T]
) -> typing.Dict[TypeModelOrEnum, T]:
    keys = filter_pydantic_models_from_set(m.keys())
    return {k: m[k] for k in keys}


def get_model_name_map(unique_models: typing.Set[type]) -> typing.Dict[type, str]:
    # this works with any class, but Pydantic types it as if it isn't
    # if this at some point breaks, we'll just implement it in this function
    return get_model_name_map_pydantic(unique_models)  # type: ignore[arg-type]


def is_sequence_like(field: ModelField) -> bool:
    return field.shape in (
        SHAPE_TUPLE,
        SHAPE_TUPLE_ELLIPSIS,
        SHAPE_LIST,
        SHAPE_SET,
        SHAPE_FROZENSET,
        SHAPE_LIST,
        SHAPE_SEQUENCE,
    )


def is_mapping_like(field: ModelField) -> bool:
    return (
        field.shape in MAPPING_LIKE_SHAPES
        or inspect.isclass(field.type_)
        and issubclass(field.type_, BaseModel)
    )


class Some(typing.Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Some({repr(self.value)})"


def get_markers_from_annotation(
    param: inspect.Parameter,
    *,
    marker_cls: typing.Type[T],
) -> typing.Generator[T, None, None]:
    if get_origin(param.annotation) is Annotated:
        # reverse the arguments so that in the case of
        # Annotated[Annotated[T, InnerDependant()], OuterDependant()]
        # we discover "outer" first
        # This is a somewhat arbitrary choice, but it is the convention we'll go with
        # See https://www.python.org/dev/peps/pep-0593/#id18 for more details
        for arg in reversed(get_args(param.annotation)):
            if isinstance(arg, marker_cls):
                yield arg
