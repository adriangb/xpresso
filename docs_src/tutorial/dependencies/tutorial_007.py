from typing import Callable, FrozenSet, Optional

from xpresso import (
    App,
    Dependant,
    FromPath,
    FromQuery,
    HTTPException,
    Operation,
    Path,
)


def require_roles(*roles: str) -> Callable[..., None]:
    role_set = frozenset(roles)

    def enforce_roles(
        roles: FromQuery[Optional[FrozenSet[str]]] = None,
    ) -> None:
        missing_roles = role_set.difference(roles or frozenset())
        if missing_roles:
            raise HTTPException(
                403, f"Missing roles: {list(missing_roles)}"
            )

    return enforce_roles


async def delete_item() -> None:
    ...


async def get_item(item_id: FromPath[str]) -> str:
    return item_id


app = App(
    routes=[
        Path(
            "/items/{item_id}",
            get=get_item,  # no extra roles required
            delete=Operation(
                endpoint=delete_item,
                dependencies=[
                    Dependant(require_roles("items-admin"))
                ],
            ),
            dependencies=[Dependant(require_roles("items-user"))],
        )
    ],
    dependencies=[Dependant(require_roles("user"))],
)
