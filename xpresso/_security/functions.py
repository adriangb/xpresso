import typing

from xpresso._security.base import SecurityBase as SecurityModel
from xpresso._security.dependants import Security as SecurityDependant
from xpresso.dependencies.models import Dependant


def Security(
    model: typing.Union[SecurityModel, typing.Type[SecurityModel]],
    *,
    scopes: typing.Optional[typing.Sequence[str]] = None,
) -> Dependant:
    if isinstance(model, SecurityModel):
        call = type(model).__call__
    else:
        call = model.__call__
    return Dependant(
        call,
        overrides={
            "self": SecurityDependant(
                dependency=model,
                scopes=scopes,
            )
        },
    )
