import typing

from di.api.providers import DependencyProvider
from di.dependant import Dependant
from di.dependant import Injectable as InjectableBase
from di.dependant import Marker

from xpresso._utils.typing import Literal

Scope = Literal["app", "connection", "endpoint"]
Scopes: typing.Tuple[Literal["app"], Literal["connection"], Literal["endpoint"]] = (
    "app",
    "connection",
    "endpoint",
)


@typing.overload
def Depends(
    call: DependencyProvider,
    *,
    use_cache: bool = ...,
    wire: bool = ...,
    sync_to_thread: bool = ...,
    scope: Scope = ...,
) -> "BoundDependsMarker":
    ...


@typing.overload
def Depends(
    *,
    use_cache: bool = ...,
    wire: bool = ...,
    sync_to_thread: bool = ...,
    scope: Scope = ...,
) -> "DependsMarker[None]":
    ...


def Depends(
    call: typing.Any = None,
    *,
    use_cache: bool = True,
    wire: bool = True,
    sync_to_thread: bool = False,
    scope: Scope = "connection",
) -> typing.Any:
    return DependsMarker(
        call=call,
        use_cache=use_cache,
        wire=wire,
        sync_to_thread=sync_to_thread,
        scope=scope,
    )


DependencyType = typing.TypeVar(
    "DependencyType", bound=typing.Optional[DependencyProvider]
)


class DependsMarker(Marker, typing.Generic[DependencyType]):
    def __init__(
        self,
        call: typing.Optional[DependencyType] = None,
        *,
        use_cache: bool = True,
        wire: bool = True,
        sync_to_thread: bool = True,
        scope: Scope = "connection",
    ) -> None:
        super().__init__(
            call=call,
            scope=scope,
            use_cache=use_cache,
            wire=wire,
            sync_to_thread=sync_to_thread,
        )

    def as_dependant(self) -> Dependant[DependencyType]:
        return Dependant(
            call=self.call,
            scope=self.scope,
            use_cache=self.use_cache,
            wire=self.wire,
            sync_to_thread=self.sync_to_thread,
            marker=self,
        )


BoundDependsMarker = DependsMarker[DependencyProvider]


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
