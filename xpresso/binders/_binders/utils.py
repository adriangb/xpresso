import contextlib
import typing

T = typing.TypeVar("T")

Consumer = typing.Callable[[T], typing.Any]
ConsumerContextManager = typing.Callable[[T], typing.AsyncContextManager[typing.Any]]


def wrap_consumer_as_cm(consumer: Consumer[T]) -> ConsumerContextManager[T]:
    @contextlib.asynccontextmanager
    async def consume(request: T) -> typing.AsyncIterator[typing.Any]:
        res = await consumer(request)
        yield res

    return consume
