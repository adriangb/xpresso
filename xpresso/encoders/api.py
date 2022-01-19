import sys
from typing import Any

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol


class Encoder(Protocol):
    def __call__(self, obj: Any) -> Any:
        ...
