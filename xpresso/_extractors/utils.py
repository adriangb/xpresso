import inspect
from typing import Iterable, Sequence, Tuple, TypeVar

from pydantic import BaseModel
from pydantic.fields import (
    MAPPING_LIKE_SHAPES,
    SHAPE_LIST,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
    ModelField,
)

T = TypeVar("T")


def grouped(items: Sequence[T], n: int = 2) -> Iterable[Tuple[T, ...]]:
    """s -> [(s0, s1, s2,...sn-1), (sn, sn+1 , sn+2,...s2n-1), ...]
    list(grouped([1, 2], 2)) == [(1, 2)]
    list(grouped([1, 2, 3, 4], 2)) == [(1, 2), (3, 4)]
    """
    if len(items) % n != 0:
        raise ValueError("items must be equally divisible by n")
    return zip(*[iter(items)] * n)


def is_sequence_like(field: ModelField) -> bool:
    return field.shape in (SHAPE_TUPLE, SHAPE_TUPLE_ELLIPSIS, SHAPE_LIST)


def is_mapping_like(field: ModelField) -> bool:
    return (
        field.shape in MAPPING_LIKE_SHAPES
        or inspect.isclass(field.type_)
        and issubclass(field.type_, BaseModel)
    )
