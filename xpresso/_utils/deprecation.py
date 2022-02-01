import typing


def not_supported(method: str) -> typing.Callable[..., typing.Any]:
    """Marks a method as not supported
    Used to hard-deprecate things from Starlette
    """

    def raise_error(*args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        raise NotImplementedError(f"Use of {method} is not supported")

    return raise_error
