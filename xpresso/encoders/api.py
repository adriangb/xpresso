from typing import Any

from xpresso._utils.compat import Protocol


class Encoder(Protocol):
    def __call__(self, obj: Any) -> Any:
        ...
