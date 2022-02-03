from typing import Any, Awaitable, Callable

from xpresso.openapi.models import SecurityScheme


class SecurityBase:
    model: SecurityScheme
    scheme_name: str
    __call__: Callable[..., Awaitable[Any]]
