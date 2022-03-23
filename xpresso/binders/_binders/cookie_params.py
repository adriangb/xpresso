import inspect
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple, cast

from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso._utils.pydantic_utils import (
    is_mapping_like,
    is_sequence_like,
    model_field_from_param,
)
from xpresso._utils.typing import Protocol
from xpresso.binders._binders.grouped import grouped
from xpresso.binders._binders.pydantic_validators import validate_param_field
from xpresso.binders.api import SupportsExtractor
from xpresso.typing import Some


def collect_sequence(value: str) -> List[str]:
    if not value:
        return []
    return [v for v in value.split(",") if v]


def collect_object(value: str) -> Dict[str, str]:
    if not value:
        return {}
    return dict(cast(Iterable[Tuple[str, str]], grouped([v for v in value.split(",")])))


def collect_scalar(value: str) -> str:
    return value


class CookieExtractor(Protocol):
    def __call__(self, value: str) -> Any:
        ...


def get_extractor(explode: bool, field: ModelField) -> CookieExtractor:
    if is_sequence_like(field):
        if explode is True:
            raise ValueError(  # pragma: no cover
                "To deserialize array cookies, you must use Cookie(explode=False)"
            )
        return collect_sequence
    if is_mapping_like(field):
        if explode is True:
            raise ValueError(  # pragma: no cover
                "To deserialize object cookies, you must use Cookie(explode=False)"
            )
        return collect_object
    # single item
    return collect_scalar


class Extractor(NamedTuple):
    name: str
    field: ModelField
    extractor: CookieExtractor

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor) and __o.name == self.name

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        param = connection.cookies.get(self.name, None)
        if param is not None:
            return await validate_param_field(
                field=self.field,
                in_="cookie",
                name=self.name,
                connection=connection,
                values=Some(self.extractor(param)),
            )
        return await validate_param_field(
            field=self.field,
            in_="cookie",
            name=self.name,
            connection=connection,
            values=None,
        )


class ExtractorMarker(NamedTuple):
    alias: Optional[str]
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        field = model_field_from_param(param)
        name = self.alias or param.name
        extractor = get_extractor(field=field, explode=self.explode)
        return Extractor(field=field, name=name, extractor=extractor)
