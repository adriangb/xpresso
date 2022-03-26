from __future__ import annotations

import typing

from di.api.providers import CallableProvider, CoroutineProvider
from di.dependant import Dependant

from xpresso.dependencies._dependencies import Depends, DependsMarker

Endpoint = typing.Union[CallableProvider[typing.Any], CoroutineProvider[typing.Any]]


class EndpointDependant(Dependant[typing.Any]):
    def __init__(
        self,
        endpoint: Endpoint,
        sync_to_thread: bool = False,
    ) -> None:
        super().__init__(
            call=endpoint,
            scope="endpoint",
            use_cache=False,
            wire=True,
            sync_to_thread=sync_to_thread,
        )

    def get_default_marker(self) -> DependsMarker[None]:
        return Depends()
