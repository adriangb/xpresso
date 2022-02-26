from __future__ import annotations

import typing

import di
from di.api.providers import DependencyProvider
from di.dependant import Injectable as InjectableBase

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


class Injectable(InjectableBase):
    __slots__ = ()

    def __init_subclass__(
        cls,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "connection",
        use_cache: bool = True,
        **kwargs: typing.Any,
    ) -> None:
        return super().__init_subclass__(call, scope, use_cache, **kwargs)


class Singleton(InjectableBase):
    __slots__ = ()

    def __init_subclass__(
        cls,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "app",
        use_cache: bool = True,
        **kwargs: typing.Any,
    ) -> None:
        return super().__init_subclass__(call, scope, use_cache, **kwargs)
