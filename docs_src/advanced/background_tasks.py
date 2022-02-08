from typing import AsyncIterator, List

import anyio
import anyio.abc

from xpresso import App, Depends, Path
from xpresso.typing import Annotated


async def create_conn_task_group() -> AsyncIterator[
    anyio.abc.TaskGroup
]:
    async with anyio.create_task_group() as tg:
        try:
            yield tg
        except Exception as e:
            print(e)
            pass
        print("exiting")


ConnectionTaskGroup = Annotated[
    anyio.abc.TaskGroup,
    Depends(create_conn_task_group, scope="connection"),
]


async def create_app_task_group() -> AsyncIterator[
    anyio.abc.TaskGroup
]:
    async with anyio.create_task_group() as tg:
        try:
            yield tg
        except Exception as e:
            print(e)
            pass
        print("exiting")


AppTaskGroup = Annotated[
    anyio.abc.TaskGroup, Depends(create_app_task_group, scope="app")
]


class Log(List[str]):
    async def log(self, msg: str) -> None:
        self.append(msg)


async def endpoint(
    log: Log, app_tg: AppTaskGroup, conn_tg: ConnectionTaskGroup
) -> None:
    app_tg.start_soon(log.log, "app")
    conn_tg.start_soon(log.log, "connection")


app = App(routes=[Path("/", get=endpoint)])
