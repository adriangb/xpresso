import inspect
import sys
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple, cast

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso.binders._extractors.api import ParameterExtractorMarker
from xpresso.binders._extractors.params.base import (
    ParameterExtractorBase,
    get_basic_param_info,
)
from xpresso.binders._extractors.utils import grouped, is_mapping_like, is_sequence_like
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


class Extractor(Protocol):
    def __call__(self, value: str) -> Any:
        ...


def get_extractor(explode: bool, field: ModelField) -> Extractor:
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


@dataclass(frozen=True)
class CookieParameterExtractor(ParameterExtractorBase):
    extractor: Extractor
    in_: ClassVar[str] = "cookie"

    def extract(self, connection: HTTPConnection) -> Any:
        param = connection.cookies.get(self.name, None)
        if param is not None:
            extracted = self.extractor(param)
            if extracted is None:
                return self.validate(None)
            return self.validate(Some(extracted))
        return self.validate(None)


@dataclass(frozen=True)
class CookieParameterExtractorMarker(ParameterExtractorMarker):
    alias: Optional[str]
    explode: bool
    in_: ClassVar[str] = "cookie"

    def register_parameter(self, param: inspect.Parameter) -> CookieParameterExtractor:
        field, name, loc = get_basic_param_info(param, self.alias, self.in_)
        extractor = get_extractor(field=field, explode=self.explode)
        return CookieParameterExtractor(
            field=field, loc=loc, name=name, extractor=extractor
        )
