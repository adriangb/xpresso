import sys

if sys.version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


from di import BaseContainer
from starlette.responses import Response


class xpressoASGIExtension(TypedDict):
    container: BaseContainer
    response: Response
