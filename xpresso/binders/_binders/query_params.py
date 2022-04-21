import inspect
from typing import Any, NamedTuple, Optional

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso._utils.pydantic_utils import model_field_from_param
from xpresso.binders._binders.formencoded_parsing import Extractor as FormExtractor
from xpresso.binders._binders.formencoded_parsing import (
    InvalidSerialization,
    get_extractor,
)
from xpresso.binders._binders.pydantic_validators import validate_param_field
from xpresso.binders.api import SupportsExtractor
from xpresso.exceptions import RequestValidationError, WebSocketValidationError

ERRORS = {
    "websocket": WebSocketValidationError,
    "http": RequestValidationError,
}


class Extractor(NamedTuple):
    name: str
    field: ModelField
    extractor: FormExtractor

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Extractor) and __o.name == self.name

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
        return await validate_param_field(
            field=self.field,
            in_="query",
            name=self.name,
            connection=connection,
            values=extracted,
        )


class ExtractorMarker(NamedTuple):
    alias: Optional[str]
    explode: bool
    style: str

    def register_parameter(self, param: inspect.Parameter) -> SupportsExtractor:
        if self.style == "deepObject" and not self.explode:
            # no such thing in the spec
            raise ValueError("deepObject can only be used with explode=True")
        field = model_field_from_param(param)
        name = self.alias or param.name
        extractor = get_extractor(style=self.style, explode=self.explode, field=field)
        name = self.alias or field.alias
        return Extractor(field=field, name=name, extractor=extractor)
