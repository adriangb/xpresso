import inspect
from dataclasses import dataclass
from typing import Any, ClassVar, Optional

from pydantic.error_wrappers import ErrorWrapper
from starlette.requests import HTTPConnection

from xpresso.binders._parameters.extractors.base import (
    ParameterExtractorBase,
    get_basic_param_info,
)
from xpresso.binders._utils.forms import Extractor, get_extractor
from xpresso.binders.api import ParameterExtractor, ParameterExtractorMarker
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError, WebSocketValidationError

ERRORS = {
    "webscoket": WebSocketValidationError,
    "http": RequestValidationError,
}


@dataclass(frozen=True)
class QueryParameterExtractor(ParameterExtractorBase):
    extractor: Extractor
    in_: ClassVar[str] = "query"

    async def extract(
        self,
        connection: HTTPConnection,
    ) -> Any:
        try:
            extracted = self.extractor(
                name=self.name, params=connection.query_params.multi_items()
            )
        except InvalidSerialization:
            raise ERRORS[connection.scope["type"]](
                [
                    ErrorWrapper(
                        exc=TypeError("Data is not a valid URL encoded query"),
                        loc=tuple(("query", self.name)),
                    )
                ]
            )
        return await self.validate(extracted, connection)


@dataclass(frozen=True)
class QueryParameterExtractorMarker(ParameterExtractorMarker):
    alias: Optional[str]
    explode: bool
    style: str
    in_: ClassVar[str] = "query"

    def register_parameter(self, param: inspect.Parameter) -> ParameterExtractor:
        if self.style == "deepObject" and not self.explode:
            # no such thing in the spec
            raise ValueError("deepObject can only be used with explode=True")
        field, name, loc = get_basic_param_info(param, self.alias, self.in_)
        extractor = get_extractor(style=self.style, explode=self.explode, field=field)
        name = self.alias or field.alias
        return QueryParameterExtractor(
            field=field, loc=loc, name=name, extractor=extractor
        )
