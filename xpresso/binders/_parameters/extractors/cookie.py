import inspect
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple, cast

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


class CookieParameterExtractor(NamedTuple):
    name: str
    field: ModelField
    extractor: CookieExtractor

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        param = connection.cookies.get(self.name, None)
        if param is not None:
            return await validate(
                field=self.field,
                in_="cookie",
                name=self.name,
                connection=connection,
                values=Some(self.extractor(param)),
            )
        return await validate(
            field=self.field,
            in_="cookie",
            name=self.name,
            connection=connection,
            values=None,
        )


class CookieParameterExtractorMarker(NamedTuple):
    alias: Optional[str]
    explode: bool

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        field = model_field_from_param(param)
        name = self.alias or param.name
        extractor = get_extractor(field=field, explode=self.explode)
        return CookieParameterExtractor(field=field, name=name, extractor=extractor)
