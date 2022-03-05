import inspect
import typing

from xpresso._utils.compat import Protocol

T = typing.TypeVar("T", covariant=True)


class SupportsMarker(Protocol[T]):
    def register_parameter(self, param: inspect.Parameter) -> T:
        ...
