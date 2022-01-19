import dataclasses
from collections import defaultdict
from enum import Enum
from pathlib import PurePath
from types import GeneratorType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

from pydantic import BaseModel
from pydantic.json import ENCODERS_BY_TYPE

from xpresso.encoders.api import Encoder
from xpresso.typing import Some

_SetIntStr = Set[Union[int, str]]
_DictIntStrAny = Dict[Union[int, str], Any]


def _generate_encoders_by_class_tuples(
    type_encoder_map: Dict[Any, Callable[[Any], Any]]
) -> Dict[Callable[[Any], Any], Tuple[Any, ...]]:
    encoders_by_class_tuples: Dict[Callable[[Any], Any], Tuple[Any, ...]] = defaultdict(
        tuple
    )
    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)
    return encoders_by_class_tuples


encoders_by_class_tuples = _generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)


class JsonableEncoder(Encoder):
    def __init__(
        self,
        include: Optional[Union[_SetIntStr, _DictIntStrAny]] = None,
        exclude: Optional[Union[_SetIntStr, _DictIntStrAny]] = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        custom_encoder: Optional[Dict[Any, Callable[[Any], Any]]] = None,
    ) -> None:
        if include is not None:
            include = set(include)
        if exclude is not None:
            exclude = set(exclude)
        self.include = include
        self.exclude = exclude
        self.by_alias = by_alias
        self.exclude_unset = exclude_unset
        self.exclude_defaults = exclude_defaults
        self.exclude_none = exclude_none
        self.custom_encoder = custom_encoder or {}

    def apply_custom_encoder(
        self, obj: Any, custom_encoder: Optional[Dict[Any, Callable[[Any], Any]]]
    ) -> Optional[Some[Any]]:
        if custom_encoder:
            key = custom_encoder.get(type(obj), None)
            if key is not None:
                return Some(key(obj))
        return None

    def __call__(
        self, obj: Any, custom_encoder: Dict[Any, Callable[[Any], Any]] = {}
    ) -> Any:
        custom_encoder = {**self.custom_encoder, **custom_encoder}
        if isinstance(obj, BaseModel):
            encoder = getattr(obj.__config__, "json_encoders", {})
            if custom_encoder:
                encoder.update(custom_encoder)
            obj_dict = obj.dict(
                include=self.include,  # type: ignore # in Pydantic
                exclude=self.exclude,  # type: ignore # in Pydantic
                by_alias=self.by_alias,
                exclude_unset=self.exclude_unset,
                exclude_none=self.exclude_none,
                exclude_defaults=self.exclude_defaults,
            )
            if "__root__" in obj_dict:
                obj_dict = obj_dict["__root__"]
            return self(obj_dict, custom_encoder=encoder)
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, PurePath):
            return str(obj)
        if isinstance(obj, (str, int, float, type(None))):
            return obj
        if isinstance(obj, dict):
            encoded_dict: Dict[Any, Any] = {}
            for key, value in cast(Mapping[Any, Any], obj).items():
                if (value is not None or not self.exclude_none) and (
                    (self.include and key in self.include)
                    or not self.exclude
                    or key not in self.exclude
                ):
                    encoded_key = self(key, custom_encoder=custom_encoder)
                    encoded_value = self(value, custom_encoder=custom_encoder)
                    encoded_dict[encoded_key] = encoded_value
            return encoded_dict
        if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
            encoded_list: List[Any] = []
            for item in cast(Sequence[Any], obj):
                encoded_list.append(self(item, custom_encoder=custom_encoder))
            return encoded_list

        custom = self.apply_custom_encoder(obj, custom_encoder=custom_encoder)
        if isinstance(custom, Some):
            return custom.value

        if type(obj) in ENCODERS_BY_TYPE:
            return ENCODERS_BY_TYPE[type(obj)](obj)
        for encoder, classes_tuple in encoders_by_class_tuples.items():
            if isinstance(obj, classes_tuple):
                return encoder(obj)

        errors: List[Exception] = []
        try:
            data = dict(obj)
        except Exception as e:
            errors.append(e)
            try:
                data = vars(obj)
            except Exception as e:
                errors.append(e)
                raise ValueError(errors)
        return self(data, custom_encoder=custom_encoder)
