from typing import Any, Sequence

from di.api.dependencies import DependantBase
from di.api.scopes import Scope


def endpoint_scope_resolver(
    dep: DependantBase[Any],
    sub_dependant_scopes: Sequence[Scope],
    _: Sequence[Scope],
) -> Scope:
    """Resolve scopes by defaulting to "connection"
    unless a sub-dependency has an "endpoint" scope
    in which case we drop down to that scope
    """
    if dep.scope is not None:
        return dep.scope
    if "endpoint" in sub_dependant_scopes:
        return "endpoint"
    return "connection"


def lifespan_scope_resolver(
    dep: DependantBase[Any],
    sub_dependant_scopes: Sequence[Scope],
    _: Sequence[Scope],
) -> Scope:
    """Always default to the "app" scope"""
    if dep.scope is None:
        return "app"
    return dep.scope
