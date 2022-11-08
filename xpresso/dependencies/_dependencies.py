import typing

from di.api.providers import DependencyProvider
from di.concurrency import as_async
from di.dependent import Dependent
from di.dependent import Injectable as InjectableBase
from di.dependent import Marker

from xpresso._utils.typing import Literal

Scope = Literal["app", "connection", "endpoint"]
Scopes = (
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
    scope: typing.Optional[Scope] = None,
) -> typing.Any:
    if sync_to_thread:
        call = as_async(call)
    return DependsMarker(
        call=call,
        use_cache=use_cache,
        wire=wire,
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
        sync_to_thread: bool = False,
        scope: typing.Optional[Scope] = None,
    ) -> None:
        super().__init__(
            call=call,
            scope=scope,
            use_cache=use_cache,
            wire=wire,
        )
        self.sync_to_thread = sync_to_thread

    def as_dependent(self) -> Dependent[DependencyType]:
        call: "typing.Optional[DependencyProvider]"
        if self.sync_to_thread:
            if not self.call:
                raise ValueError(
                    "sync_to_thread can only be used if you explicitly declare the target function"
                )
            call = as_async(self.call)
        else:
            call = self.call
        return Dependent(
            call=call,  # type: ignore
            scope=self.scope,
            use_cache=self.use_cache,
            wire=self.wire,
            marker=self,
        )


BoundDependsMarker = DependsMarker[DependencyProvider]


class Injectable(InjectableBase):
    __slots__ = ()

    def __init_subclass__(
        cls,
        call: typing.Optional[DependencyProvider] = None,
        scope: typing.Optional[Scope] = None,
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
