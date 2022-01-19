import typing

from di import Dependant

from xpresso.security._base import SecurityBase as SecurityModel
from xpresso.security._dependants import Security as SecurityDependant


def Security(
    model: typing.Union[SecurityModel, typing.Type[SecurityModel]],
    *,
    scopes: typing.Optional[typing.Sequence[str]] = None,
) -> Dependant[typing.Any]:
    if isinstance(model, SecurityModel):
        call = type(model).__call__
    else:
        call = model.__call__
    return Dependant[typing.Any](
        call,
        scope="connection",
        overrides={
            "self": SecurityDependant(
                dependency=model,
                scopes=scopes,
            )
        },
    )
