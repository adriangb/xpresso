from __future__ import annotations

from typing import Optional, Sequence, Union, cast

from di.api.providers import DependencyProviderType

from xpresso.dependencies.models import Dependant
from xpresso.security._base import SecurityBase


class Security(Dependant):
    _dependency: Union[DependencyProviderType[SecurityBase], SecurityBase]

    def __init__(
        self,
        dependency: Union[DependencyProviderType[SecurityBase], SecurityBase],
        *,
        scopes: Optional[Sequence[str]] = None,
    ):
        self._dependency = dependency
        if isinstance(dependency, SecurityBase):

            async def call() -> SecurityBase:
                return dependency  # type: ignore[return-value]

            super().__init__(call, scope="app")
        else:
            super().__init__(dependency, scope="app")
        self.scopes = frozenset(scopes or [])

    def __hash__(self) -> int:
        return hash((self._dependency, self.scopes))

    def __eq__(self, o: object) -> bool:
        if type(self) != type(o):
            return False
        o = cast(Security, o)
        return (self._dependency, self.scopes) == (o._dependency, o.scopes)
