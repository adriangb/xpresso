from __future__ import annotations

import typing

from di.api.providers import DependencyProvider
from di.dependant import Dependant
from di.dependant import Injectable as InjectableBase
from di.dependant import Marker

from xpresso._utils.compat import Literal

T = typing.TypeVar("T")


Scope = Literal["app", "connection", "endpoint"]
Scopes: typing.Tuple[Literal["app"], Literal["connection"], Literal["endpoint"]] = (
    "app",
    "connection",
    "endpoint",
)


class Depends(Marker):
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

    def as_dependant(self) -> Dependant[typing.Any]:
        return Dependant(
            call=self.call,
            scope=self.scope,
            use_cache=self.use_cache,
            wire=self.wire,
            sync_to_thread=self.sync_to_thread,
            marker=self,
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
