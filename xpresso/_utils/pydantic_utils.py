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

T = typing.TypeVar("T")


def model_field_from_param(
    param: inspect.Parameter, alias: typing.Optional[str] = None
) -> ModelField:
    return ModelField.infer(
        name=alias or param.name,
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
