from di import BaseContainer
from starlette.responses import Response

from xpresso._utils.compat import TypedDict


class _XpressoASGIExtension(TypedDict):
    container: BaseContainer
    response_sent: bool


class XpressoASGIExtension(_XpressoASGIExtension, total=False):
    response: Response
