import sys

if sys.version_info < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict


from di.api.container import ContainerProtocol
from starlette.responses import Response


class xpressoASGIExtension(TypedDict):
    container: ContainerProtocol
    response: Response
