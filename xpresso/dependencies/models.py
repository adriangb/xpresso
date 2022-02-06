from __future__ import annotations

import inspect
import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import di
from di.api.providers import DependencyProvider

T = typing.TypeVar("T")


Scope = Literal["app", "connection", "endpoint"]


class Depends(di.Dependant[typing.Any]):
    __slots__ = ()
    scope: Scope

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

    def initialize_sub_dependant(self, param: inspect.Parameter) -> Depends:
        if param.default is param.empty:
            # try to auto-wire
            return Depends(
                call=None,
                scope=self.scope,
                use_cache=self.use_cache,
            )
        # has a default parameter but we create a dependency anyway just for binds
        # but do not wire it to make autowiring less brittle and less magic
        return Depends(
            call=None,
            scope=self.scope,
            use_cache=self.use_cache,
            wire=False,
        )
