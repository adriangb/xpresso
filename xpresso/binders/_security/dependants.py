from __future__ import annotations

from typing import Optional, Sequence, Union

from di.api.providers import DependencyProviderType

from xpresso.binders.api import SecurityBase
from xpresso.dependencies.models import Dependant


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

    @property
    def cache_key(self) -> Union[DependencyProviderType[SecurityBase], SecurityBase]:
        return self._dependency
