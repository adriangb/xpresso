from typing import Any

from di.dependant import Injectable
from pydantic import BaseSettings

from xpresso.dependencies.models import Scope


class Config(Injectable, BaseSettings):
    def __init_subclass__(
        cls, scope: Scope = "app", use_cache: bool = True, **kwargs: Any
    ) -> None:
        # Pydantic BaseSettings models cannot be wired because of how the grab values
        # from env vars
        # But most of the time you just want to load the entire thing from the environment,
        # so that's what we do here
        def call() -> Any:
            return cls()

        return super().__init_subclass__(
            call=call, scope=scope, use_cache=use_cache, **kwargs
        )
