# Dependency Lifecycle

Up until now we've only seen dependencies that return a value directly.
But often you'll want to do some work (like creating a database connection), **yield** that thing (the connection object) and then do some more work to **teardown** that thing (for example closing the connection).

Xpresso lets you declare this type of execution using **context manager dependencies**.

These are dependencies that use the **yield** keyword **once** to give back control and then wait until they get back control to run their **teardown**.

!!! note "Note"
    Any function `func()` that could be passed to [@contextlib.contextmanager] or [@contextlib.asynccontextmanager] will work.

We can apply this concept to our `httpx.AsyncClient` example to clean up the client after we are done using it.
All we have to do is change our function to be a context manager like function (an async one in this case) and then use `httpx.AsyncClient`'s context manager within the function:

```python hl_lines="20-22"
--8<-- "docs_src/tutorial/dependencies/tutorial_004.py"
```

!!! check
    Did you notice that we also converted `get_client()` from a `def` function to an `async def` function?
    Making changes like this is super easy using Xpresso's dependency injection system!
    It decouples you from execution so that you can mix and match sync and async dependencies without worrying about `await`ing from a sync dependency and other complexities of cooperative concurrency.

!!! tip "Tip"
    It is always best to use `httpx.AsyncClient` as a context manager to ensure that connections get cleaned up.
    Otherwise, httpx will give you a warning which you'd see in your logs.

Once again, nothing will change from the application user's perspective, but our backend is now a lot more resilient!

The order of execution here is `get_client() -> echo_headers() -> get_client()` and is roughly equivalent to:

```python
async with asynccontextmanager(get_client(HttpBinConfigModel())) as client:
    await echo_headers(client)
```

[@contextlib.contextmanager]: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager
[@contextlib.asynccontextmanager]: https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager
