import inspect
import typing

from starlette.requests import HTTPConnection

from xpresso import status
from xpresso._utils.compat import Literal
from xpresso._utils.typing import model_field_from_param
from xpresso.binders.api import SecurityExtractor
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
)


Extractor = typing.Callable[[HTTPConnection, str], typing.Optional[str]]


def from_header(conn: HTTPConnection, name: str) -> typing.Optional[str]:
    return conn.headers.get(name, None)


def from_query(conn: HTTPConnection, name: str) -> typing.Optional[str]:
    return conn.query_params.get(name, None)


def from_cookie(conn: HTTPConnection, name: str) -> typing.Optional[str]:
    return conn.cookies.get(name, None)


EXTRACTORS = {
    "header": from_header,
    "query": from_query,
    "cookie": from_cookie,
}


class APIKeyExtractor(typing.NamedTuple):
    required: bool
    name: str
    extractor: Extractor

    def extract(self, conn: HTTPConnection) -> typing.Optional[str]:
        api_key = self.extractor(conn, self.name)
        if api_key is None and self.required:
            raise UNAUTHORIZED_EXC
        return api_key


class APIKeyExtractorMarker:
    def __init__(self, in_: Literal["header", "query", "cookie"], name: str) -> None:
        self.in_ = in_
        self.name = name

    def register_parameter(self, param: inspect.Parameter) -> SecurityExtractor:
        extractor = EXTRACTORS[self.in_]
        required = model_field_from_param(param).required is not False
        return APIKeyExtractor(required=required, name=self.name, extractor=extractor)
