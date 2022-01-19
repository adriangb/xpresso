import time

import anyio

from xpresso import App, Dependant, Operation, Path


def slow_dependency_1() -> None:
    time.sleep(0.1)


async def slow_dependency_2() -> None:
    await anyio.sleep(0.1)


async def endpoint() -> None:
    ...


app = App(
    routes=[
        Path(
            "/slow",
            get=Operation(
                endpoint=endpoint,
                dependencies=[
                    Dependant(slow_dependency_1, sync_to_thread=True),
                    Dependant(slow_dependency_2),
                ],
                execute_dependencies_concurrently=True,
            ),
        )
    ]
)
