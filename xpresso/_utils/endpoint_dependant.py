from __future__ import annotations

import typing

import di
from di.api.providers import CallableProvider, CoroutineProvider

from xpresso.dependencies.models import Depends

T = typing.TypeVar("T")

Endpoint = typing.Union[CallableProvider[typing.Any], CoroutineProvider[typing.Any]]


class EndpointDependant(di.Dependant[typing.Any]):
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

    def get_default_marker(self) -> Depends:
        return Depends()
