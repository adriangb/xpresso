from __future__ import annotations

import sys
import typing

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import di
import di.dependant
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProvider

T = typing.TypeVar("T")


Scope = Literal["app", "connection", "endpoint"]


class Dependant(di.Dependant[typing.Any]):
    __slots__ = ()

    def __init__(
        self,
        call: typing.Optional[DependencyProvider] = None,
        scope: Scope = "endpoint",
        share: bool = True,
        wire: bool = True,
        overrides: typing.Optional[
            typing.Mapping[str, DependantBase[typing.Any]]
        ] = None,
    ) -> None:
        super().__init__(
            call=call,
            scope=scope,
            share=share,
            wire=wire,
            overrides=overrides,
        )
