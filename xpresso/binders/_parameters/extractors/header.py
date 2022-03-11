import functools
import inspect
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple, cast

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso._utils.compat import Protocol
from xpresso._utils.typing import (
    is_mapping_like,
    is_sequence_like,
    model_field_from_param,
)
from xpresso.binders._parameters.extractors.validator import validate
from xpresso.binders._utils.grouped import grouped
from xpresso.binders.api import SupportsExtractor
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError, WebSocketValidationError
from xpresso.typing import Some


def collect_scalar(value: Optional[str]) -> Optional[Some]:
    if value is None:
        return None
    split = value.split(",")
    if len(split) == 1:
        return Some(split[0])
    return Some(next(iter(split)))


def collect_sequence(value: Optional[str]) -> Optional[Some]:
    if not value:
        return Some(cast(List[str], []))
    return Some([v.lstrip() for v in value.split(",")])


def collect_object(
    explode: bool,
    value: Optional[str],
) -> Optional[Some]:
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


class HeaderExtractor(Protocol):
    def __call__(self, value: Optional[str]) -> Optional[Some]:
        ...


def get_extractor(explode: bool, field: ModelField) -> HeaderExtractor:
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


class HeaderParameterExtractor(NamedTuple):
    name: str
    field: ModelField
    extractor: HeaderExtractor
    header_name: bytes

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        # parse headers according to RFC 7230
        # this means treating repeated headers and "," seperated ones the same
        # so here we merge them all into one "," seperated string for consistency
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
        return await validate(
            field=self.field,
            in_="header",
            name=self.name,
            connection=connection,
            values=extracted,
        )


class HeaderParameterExtractorMarker(NamedTuple):
    alias: Optional[str]
    explode: bool
    convert_underscores: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        field = model_field_from_param(param)
        name = self.alias or param.name
        if self.convert_underscores and not self.alias and field.name == field.alias:
            name = name.replace("_", "-")
        extractor = get_extractor(explode=self.explode, field=field)
        return HeaderParameterExtractor(
            field=field,
            name=name,
            extractor=extractor,
            header_name=name.lower().encode("latin-1"),
        )
