from __future__ import annotations

import typing

from di.api.providers import CallableProvider, CoroutineProvider
from di.concurrency import as_async
from di.dependent import Dependent

from xpresso.dependencies._dependencies import Depends, DependsMarker

Endpoint = typing.Union[CallableProvider[typing.Any], CoroutineProvider[typing.Any]]


class EndpointDependent(Dependent[typing.Any]):
    def __init__(
        self,
        endpoint: Endpoint,
        sync_to_thread: bool = False,
    ) -> None:
        if sync_to_thread:
            endpoint = as_async(endpoint)
        super().__init__(
            call=endpoint,
            scope="endpoint",
            use_cache=False,
            wire=True,
        )

    def get_default_marker(self) -> DependsMarker[None]:
        return Depends()
