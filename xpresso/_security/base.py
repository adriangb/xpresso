from typing import Any, Awaitable, Callable

from xpresso.openapi.models import SecurityBase as SecurityBaseModel


class SecurityBase:
    model: SecurityBaseModel
    scheme_name: str
    __call__: Callable[..., Awaitable[Any]]
