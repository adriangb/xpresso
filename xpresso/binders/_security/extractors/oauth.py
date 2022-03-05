import inspect
import typing

from starlette.requests import HTTPConnection

from xpresso import status
from xpresso._utils.typing import model_field_from_param
from xpresso.binders.api import SecurityExtractor
from xpresso.exceptions import HTTPException

UNAUTHORIZED_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_authorization_scheme_param(
    authorization_header_value: str,
) -> typing.Tuple[str, str]:
    if not authorization_header_value:
        return "", ""
    scheme, _, param = authorization_header_value.partition(" ")
    return scheme, param


class OAuth2Token(typing.NamedTuple):
    token: str
    required_scopes: typing.FrozenSet[str]


class OAuth2Extractor(typing.NamedTuple):
    required: bool
    required_scopes: typing.FrozenSet[str]

    def extract(self, conn: HTTPConnection) -> typing.Optional[OAuth2Token]:
        authorization_header = conn.headers.get("Authorization", None)
        if authorization_header:
            scheme, param = get_authorization_scheme_param(authorization_header)
            if scheme == "Bearer":
                return OAuth2Token(param, self.required_scopes)
            else:
                raise UNAUTHORIZED_EXC
        if self.required:
            raise UNAUTHORIZED_EXC
        return None


class OAuth2ExtractorMarker(typing.NamedTuple):
    required_scopes: typing.FrozenSet[str]

    def register_parameter(self, param: inspect.Parameter) -> SecurityExtractor:
        return OAuth2Extractor(
            required=model_field_from_param(param).required is not False,
            required_scopes=self.required_scopes,
        )
