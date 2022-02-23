from __future__ import annotations

import inspect
import typing

import di
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProvider
from di.dependant import InjectableClass

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
        child_scope: Scope = "app" if self.scope == "app" else "connection"
        if param.default is param.empty:
            return Depends(scope=child_scope).register_parameter(param)
        # create a dependency marker so that we can apply binds
        # but default to using the default value if there are no binds
        return Depends(scope=child_scope, wire=False).register_parameter(param)


class Injectable(InjectableClass):
    __slots__ = ()

    def __init_subclass__(
        cls,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "connection",
        use_cache: bool = True,
        **kwargs: typing.Any,
    ) -> None:
        return super().__init_subclass__(call, scope, use_cache, **kwargs)


class Singleton(Injectable):
    __slots__ = ()

    def __init_subclass__(
        cls,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "app",
        use_cache: bool = True,
        **kwargs: typing.Any,
    ) -> None:
        return super().__init_subclass__(call, scope, use_cache, **kwargs)
