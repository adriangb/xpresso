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

from xpresso._utils.typing import is_mapping_like, is_sequence_like
from xpresso.binders._parameters.extractors.base import (
    ParameterExtractorBase,
    get_basic_param_info,
)
from xpresso.binders._utils.grouped import grouped
from xpresso.binders.api import ParameterExtractor, ParameterExtractorMarker
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError, WebSocketValidationError
from xpresso.typing import Some


def collect_scalar(value: Optional[str]) -> Optional[Some[str]]:
    if value is None:
        return None
    split = value.split(",")
    if len(split) == 1:
        return Some(split[0])
    return Some(next(iter(split)))


def collect_sequence(value: Optional[str]) -> Optional[Some[List[str]]]:
    if not value:
        return Some(cast(List[str], []))
    return Some([v.lstrip() for v in value.split(",")])


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
            res[name.lstrip()] = val
        return Some(res)
    try:
        groups = cast(
            Iterable[Tuple[str, str]], grouped([v.lstrip() for v in value.split(",")])
        )
    except ValueError:
        raise InvalidSerialization(f"invalid object style header: {value}")
    return Some(dict(groups))


class Extractor(Protocol):
    def __call__(self, value: Optional[str]) -> Optional[Some[Any]]:
        ...


def get_extractor(explode: bool, field: ModelField) -> Extractor:
    # form style
    if is_sequence_like(field):
        return collect_sequence
    if is_mapping_like(field):
        return functools.partial(collect_object, explode)
    # single item
    return collect_scalar


ERRORS = {
    "webscoket": WebSocketValidationError,
    "http": RequestValidationError,
}


@dataclass(frozen=True)
class HeaderParameterExtractor(ParameterExtractorBase):
    extractor: Extractor
    in_: ClassVar[str] = "header"
    header_name: bytes

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        # parse headers according to RFC 7230
        # this means treating repeated headers and "," seperated ones the same
        # so here we merge them all into one "," seperated string
        # also note that whitespaces after a "," don't matter, so we .lstrip() as needed
        header_values: "List[str]" = []
        for name, value in connection.scope["headers"]:
            if name == self.header_name:
                header_values.append(value.decode("latin-1"))
        header_value: "Optional[str]"
        if header_values:
            header_value = ",".join(header_values)
        else:
            header_value = None
        try:
            extracted = self.extractor(header_value)
        except InvalidSerialization as exc:
            raise ERRORS[connection.scope["type"]](
                [ErrorWrapper(exc=exc, loc=("header", self.name))]
            )
        return await self.validate(extracted, connection)


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
            field=field,
            loc=loc,
            name=name,
            extractor=extractor,
            header_name=name.lower().encode("latin-1"),
        )
