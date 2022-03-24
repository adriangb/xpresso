import functools
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    cast,
)

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso._utils.pydantic_utils import (
    is_mapping_like,
    is_sequence_like,
    model_field_from_param,
)
from xpresso.binders._binders.grouped import grouped
from xpresso.binders._binders.pydantic_validators import validate_param_field
from xpresso.binders.api import SupportsExtractor
from xpresso.exceptions import RequestValidationError, WebSocketValidationError
from xpresso.typing import Some


class InvalidSerialization(Exception):
    pass


def collect_scalar(name: str, style: str, explode: bool, value: str) -> str:
    if style == "simple":
        return value
    if style == "label":
        if not value.startswith("."):
            raise InvalidSerialization("label serialized parameter must start with '.'")
        return value[1:]
    # style == "matrix"
    template = f";{name}="
    if not value.startswith(template):
        raise InvalidSerialization(
            f"matrix serialized parameter must start with {template}"
        )
    return value[len(template) :]


def collect_sequence(name: str, style: str, explode: bool, value: str) -> List[str]:
    if style == "simple":
        return value.split(",")
    if style == "label":
        if value[0] != ".":
            raise InvalidSerialization("label serialized parameter must start with '.'")
        if explode:
            return value[1:].split(".")
        return value[1:].split(",")
    # style == "matrix"
    template = f";{name}="
    if not value.startswith(template):
        raise InvalidSerialization(
            f"matrix serialized parameter must start with {template}"
        )
    if explode:
        return value.split(template)[1:]
    return value.split(template, maxsplit=1)[1].split(",")


def collect_object(
    name: str,
    style: str,
    explode: bool,
    value: str,
) -> Dict[str, str]:
    if style == "simple":
        delimiter = ","
    elif style == "label":
        value = value[1:]
        if explode:
            delimiter = "."
        else:
            delimiter = ","
    else:  # style == "matrix"
        if explode:
            if value[0] != ";":
                raise InvalidSerialization(
                    "object-valued path parameter could be deserialized"
                    f" with style=matrix, explode=True: {value}"
                )
            value = value[1:]
            delimiter = ";"
        else:
            value = value[len(f";{name}=") :]
            delimiter = ","
    if explode:
        res: Dict[str, str] = {}
        for field in value.split(delimiter):
            split = field.split("=", maxsplit=1)
            if len(split) != 2:
                raise InvalidSerialization(f"{field} is not a valid field encoding")
            name, val = field.split("=", maxsplit=1)
            res[name] = val
        return res
    return dict(cast(Iterable[Tuple[str, str]], grouped(value.split(delimiter))))


def get_extractor(style: str, explode: bool, field: ModelField) -> Callable[..., Any]:
    # form style
    if is_sequence_like(field):
        return functools.partial(
            collect_sequence,
            style=style,
            explode=explode,
        )
    if is_mapping_like(field):
        return functools.partial(
            collect_object,
            style=style,
            explode=explode,
        )
    # single item
    return functools.partial(
        collect_scalar,
        style=style,
        explode=explode,
    )


ERRORS = {
    "webscoket": WebSocketValidationError,
    "http": RequestValidationError,
}


class Extractor(NamedTuple):
    name: str
    field: ModelField
    extractor: Callable[..., Any]

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor) and __o.name == self.name

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        param_value: str = connection.path_params[self.name]  # type: ignore[assignment]
        try:
            extracted = self.extractor(name=self.name, value=param_value)
        except InvalidSerialization as exc:
            raise ERRORS[connection.scope["type"]](
                [ErrorWrapper(exc=exc, loc=("path", self.name))]
            )
        return await validate_param_field(
            field=self.field,
            in_="path",
            name=self.name,
            connection=connection,
            values=Some(extracted),
        )


class ExtractorMarker(NamedTuple):
    alias: Optional[str]
    explode: bool
    style: str

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        field = model_field_from_param(param)
        name = self.alias or param.name
        extractor = get_extractor(style=self.style, explode=self.explode, field=field)
        return Extractor(field=field, name=name, extractor=extractor)
