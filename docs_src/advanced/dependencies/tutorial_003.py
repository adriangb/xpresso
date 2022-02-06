from xpresso import App, Depends, Path
from xpresso.typing import Annotated


class SharedDependency:
    pass


def dependency_1(shared: SharedDependency) -> SharedDependency:
    return shared


def dependency_2(shared: SharedDependency) -> SharedDependency:
    return shared


async def endpoint(
    shared1: Annotated[SharedDependency, Depends(dependency_1)],
    shared2: Annotated[SharedDependency, Depends(dependency_1)],
    shared3: Annotated[SharedDependency, Depends(use_cache=False)],
) -> None:
    assert shared1 is shared2
    assert shared1 is not shared3


app = App(
    routes=[
        Path(
            "/shared",
            get=endpoint,
        )
    ]
)
