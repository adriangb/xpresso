import contextlib
import inspect
import typing
from types import TracebackType

from di.api.dependencies import DependantBase
from di.api.providers import DependencyProvider
from di.container import Container
from di.dependant import Dependant

from xpresso._utils.compat import Annotated, get_args, get_origin


def get_type(param: inspect.Parameter) -> type:
    if get_origin(param.annotation) is Annotated:
        return next(iter(get_args(param.annotation)))
    return param.annotation


class DependencyOverrideManager:
    _stacks: typing.List[contextlib.ExitStack]

    def __init__(self, container: Container) -> None:
        self._container = container
        self._stacks = []

    def __setitem__(
        self, target: DependencyProvider, replacement: DependencyProvider
    ) -> None:
        def hook(
            param: typing.Optional[inspect.Parameter],
            dependant: DependantBase[typing.Any],
        ) -> typing.Optional[DependantBase[typing.Any]]:
            if not isinstance(dependant, Dependant):
                return None
            scope = dependant.scope
            dep = Dependant(
                replacement,
                scope=scope,  # type: ignore[arg-type]
                use_cache=dependant.use_cache,
                wire=dependant.wire,
                sync_to_thread=dependant.sync_to_thread,
            )
            if param is not None and param.annotation is not param.empty:
                type_ = get_type(param)
                if type_ is target:
                    return dep
            if dependant.call is not None and dependant.call is target:
                return dep
            return None

        cm = self._container.bind(hook)
        if self._stacks:
            self._stacks[-1].enter_context(cm)

    def __enter__(self) -> "DependencyOverrideManager":
        self._stacks.append(contextlib.ExitStack().__enter__())
        return self

    def __exit__(
        self,
        __exc_type: typing.Optional[typing.Type[BaseException]],
        __exc_value: typing.Optional[BaseException],
        __traceback: typing.Optional[TracebackType],
    ) -> typing.Optional[bool]:
        return self._stacks.pop().__exit__(__exc_type, __exc_value, __traceback)
