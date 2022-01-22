from __future__ import annotations

import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import di
from di.api.providers import DependencyProvider

T = typing.TypeVar("T")


Scope = Literal["app", "connection", "operation"]


class Dependant(di.Dependant[typing.Any]):
    __slots__ = ()

    def __init__(
        self,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "connection",
        use_cache: bool = True,
        wire: bool = True,
        sync_to_thread: bool = False,
    ) -> None:
        super().__init__(
            call=call,
            scope=scope,
            use_cache=use_cache,
            wire=wire,
            sync_to_thread=sync_to_thread,
        )
