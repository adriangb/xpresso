import time

from xpresso import App, Dependant, Operation, Path


def slow_dependency() -> None:
    time.sleep(1e-3)


def slow_endpoint() -> None:
    time.sleep(1e-3)


app = App(
    routes=[
        Path(
            "/slow",
            get=Operation(
                endpoint=slow_endpoint,
                sync_to_thread=True,
                dependencies=[
                    Dependant(slow_dependency, sync_to_thread=True)
                ],
            ),
        )
    ]
)
