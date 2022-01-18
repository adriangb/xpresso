import sys
from typing import Generic, TypeVar

if sys.version_info < (3, 9):
    from typing_extensions import Annotated as Annotated  # noqa: F401
else:
    from typing import Annotated as Annotated  # noqa: F401

T = TypeVar("T")


class Some(Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Some({repr(self.value)})"
