from __future__ import annotations

import inspect
import typing

import di
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProvider

from xpresso._utils.compat import Literal

T = typing.TypeVar("T")


Scope = Literal["app", "connection", "endpoint"]


class Depends(di.Marker, di.Dependant[typing.Any]):
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

    def from_callable(
        self, call: typing.Optional[DependencyProvider]
    ) -> DependantBase[typing.Any]:
        return Depends(
            call=call,
            scope=self.scope,
            use_cache=self.use_cache,
            wire=self.wire,
            sync_to_thread=self.sync_to_thread,
        )

    def initialize_sub_dependant(
        self, param: inspect.Parameter
    ) -> DependantBase[typing.Any]:
        if param.default is param.empty:
            # try to auto-wire
            return Depends(
                call=None,
                scope=self.scope,
                use_cache=self.use_cache,
            ).register_parameter(param)
        # has a default parameter but we create a dependency anyway just for binds
        # but do not wire it to make autowiring less brittle and less magic
        return Depends(
            call=None,
            scope=self.scope,
            use_cache=self.use_cache,
            wire=False,
        ).register_parameter(param)
