import time

import anyio

from xpresso import App, Depends, Operation, Path


def slow_dependency_1() -> None:
    time.sleep(1)


async def slow_dependency_2() -> None:
    await anyio.sleep(1)


async def endpoint() -> None:
    ...


app = App(
    routes=[
        Path(
            "/slow",
            get=Operation(
                endpoint=endpoint,
                dependencies=[
                    Depends(slow_dependency_1, sync_to_thread=True),
                    Depends(slow_dependency_2),
                ],
                execute_dependencies_concurrently=True,
            ),
        )
    ]
)
