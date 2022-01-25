import sys

if sys.version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


from di import BaseContainer
from starlette.responses import Response


class _XPressoASGIExtension(TypedDict):
    container: BaseContainer
    response_sent: bool


class XPressoASGIExtension(_XPressoASGIExtension, total=False):
    response: Response
