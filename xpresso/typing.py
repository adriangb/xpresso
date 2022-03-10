import sys
from typing import Any, NamedTuple

if sys.version_info < (3, 9):
    from typing_extensions import Annotated as Annotated  # noqa: F401
else:
    from typing import Annotated as Annotated  # noqa: F401


class Some(NamedTuple):
    value: Any
