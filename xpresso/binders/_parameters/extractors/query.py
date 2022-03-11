import inspect
from typing import Any, NamedTuple, Optional

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import HTTPConnection

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._parameters.extractors.validator import validate
from xpresso.binders._utils.forms import Extractor as FormExtractor
from xpresso.binders._utils.forms import get_extractor
from xpresso.binders.api import SupportsExtractor
from xpresso.binders.exceptions import InvalidSerialization
from xpresso.exceptions import RequestValidationError, WebSocketValidationError

ERRORS = {
    "webscoket": WebSocketValidationError,
    "http": RequestValidationError,
}


class QueryParameterExtractor(NamedTuple):
    name: str
    field: ModelField
    extractor: FormExtractor

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
        return await validate(
            field=self.field,
            in_="query",
            name=self.name,
            connection=connection,
            values=extracted,
        )


class QueryParameterExtractorMarker(NamedTuple):
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
        return QueryParameterExtractor(field=field, name=name, extractor=extractor)
