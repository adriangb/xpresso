import functools
import inspect
import sys
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple, cast

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso.binders._extractors.api import ParameterExtractor, ParameterExtractorMarker
from xpresso.binders._extractors.exceptions import InvalidSerialization
from xpresso.binders._extractors.params.base import (
    ParameterExtractorBase,
    get_basic_param_info,
)
from xpresso.binders._extractors.utils import grouped, is_mapping_like, is_sequence_like
from xpresso.exceptions import RequestValidationError
from xpresso.typing import Some


def collect_sequence(value: Optional[str]) -> Optional[Some[List[str]]]:
    if not value:
        return Some(cast(List[str], []))
    return Some(value.split(","))


def collect_object(
    explode: bool,
    value: Optional[str],
) -> Optional[Some[Dict[str, str]]]:
    if not value:
        return None
    if explode:
        res: Dict[str, str] = {}
        for field in value.split(","):
            split = field.split("=", maxsplit=1)
            if len(split) == 1 or not field or field[0] == "=":
                raise InvalidSerialization(f"invalid object style header: {value}")
            name, val = split
            res[name] = val
        return Some(res)
    try:
        groups = cast(Iterable[Tuple[str, str]], grouped(value.split(",")))
    except ValueError:
        raise InvalidSerialization(f"invalid object style header: {value}")
    return Some(dict(groups))


class Extractor(Protocol):
    def __call__(self, value: str) -> Optional[Some[Any]]:
        ...


def get_extractor(explode: bool, field: ModelField) -> Extractor:
    # form style
    if is_sequence_like(field):
        return collect_sequence
    if is_mapping_like(field):
        return functools.partial(collect_object, explode)
    # single item
    return lambda value: Some(value) if value is not None else None


@dataclass(frozen=True)
class HeaderParameterExtractor(ParameterExtractorBase):
    extractor: Extractor
    in_: ClassVar[str] = "header"

    def extract(self, connection: HTTPConnection) -> Any:
        param_value = connection.headers.get(self.name, None)
        try:
            extracted = self.extractor(param_value)
        except InvalidSerialization as exc:
            raise RequestValidationError(
                [ErrorWrapper(exc=exc, loc=("header", self.name))]
            )
        return self.validate(extracted)


@dataclass(frozen=True)
class HeaderParameterExtractorMarker(ParameterExtractorMarker):
    alias: Optional[str]
    explode: bool
    convert_underscores: bool
    in_: ClassVar[str] = "header"

    def register_parameter(self, param: inspect.Parameter) -> ParameterExtractor:
        field, name, loc = get_basic_param_info(param, self.alias, self.in_)
        if self.convert_underscores and not self.alias and field.name == field.alias:
            name = name.replace("_", "-")
        extractor = get_extractor(explode=self.explode, field=field)
        return HeaderParameterExtractor(
            field=field, loc=loc, name=name, extractor=extractor
        )
