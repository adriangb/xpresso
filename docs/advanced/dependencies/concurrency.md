
# Dependency Concurrency

Xpresso's dependency injection system lets you mix and match sync and async dependencies, use dependencies with teardown and control parallelization of dependency execution.
If you want to get the best performance out of your system, you should understand how all of these features interact and profile different arrangements until you find the one that performs the best for you.

## Sync vs. Async

The dependency injection system lets you mix and match sync and async dependencies.
That is, a sync dependency can depend on an async one and vise versa.

The main thing to keep in mind here is that by default dependencies are all executed in the same thread and event loop.
This means that **sync dependencies will block the event loop**: a single sync dependency doing IO can bring your app to a grinding halt and make it unable to serve concurrent requests to other users.

Fortunately, this is not a problem for many sync dependencies: if you are just loading a config from environment variables or otherwise not doing IO, your sync dependency won't "block" the event loop and your app will run fine.
When you really need to start worrying about things is if you are doing database IO with a synchronous database client or something like that.
For these cases, Xpresso provides a `sync_to_thread` argument to `Dependant` as well as `Operation`.
This will move execution of this dependency or endpoint function into a thread so that it can do IO concurrently and not block your application.
For example, let's make a sync endpoint and sync dependencies that call `time.sleep()` to simulate some sort of blocking IO:

```python hl_lines="6-7 10-11"
--8<-- "docs_src/advanced/dependencies/tutorial_001.py"
```

All we have to do is pass `sync_to_thread=True` in the right place to signal that the endpoint function or dependency should be executed in a thread:

```python hl_lines="18-22"
--8<-- "docs_src/advanced/dependencies/tutorial_001.py"
```

The endpoint will still take ~200ms to return a result, but at least it won't block the entire application from handling other requests.

!!! tip
    This does not do anything about the [global interpreter lock] (GIL).
    Long running CPU bound computation, like inference on a machine learning model, will still block your application (it will block the entire Python process).
    For these situations, consider using [Gunicorn] to manage multiple processes or create a subprocess manually just for that CPU intensive computation.

!!! warning
    There is an overhead to using `sync_to_thread`, hence why it is not the default.
    Do not blindly use it on every sync dependency, profile first!

## Parallel execution

Xpresso is capable of parallelizing execution of dependencies.
For example, if you have a dependency that gets the current user from the database and another that (independently) makes an HTTP request to an authorization server to check if the user's credentials are still active, these can be executed in parallel.
If each dependency takes 100ms to execute, this means together they will only take ~100ms to execute instead of 200ms.
The key is that there must be no interdependence between them and they must both be IO bound (including sync dependencies marked with `sync_to_thread`).

To turn on parallel execution of dependencies, use the `execute_dependencies_concurrently` argument to `Operation`.
First we'll define two placeholder dependencies that do not depend on each other:

```python hl_lines="8-9 12-13"
--8<-- "docs_src/advanced/dependencies/tutorial_002.py"
```

Then we'll create an Operation that uses these two dependencies:

```python hl_lines="26-29"
--8<-- "docs_src/advanced/dependencies/tutorial_002.py"
```

And finally we pass `execute_dependencies_concurrently=True` to Operation:

```python hl_lines="30"
--8<-- "docs_src/advanced/dependencies/tutorial_002.py"
```

That's it!
Now this endpoint will take ~0.1s to execute instead of 0.2s.

!!! tip
    You can only enable or disable parallel execution for an entire Operation.
    This can't be applied to groups of dependencies individually.

!!! note
    There is no guarantee of ordering of execution.
    The most efficient execution path is calculated at runtime using the algorithm described in the standard library's [graphlib] re-implemented in Rust by [graphlib2].
    The actual concurrency is enabled by [anyio TaskGroups].

!!! warning
    There is overhead to enabling this feature.
    For simple endpoints that don't benefit from parallelization of dependency execution, this will likely _hurt_ performance.
    Always profile before applying this option!

!!! attention
    Teardowns are never executed concurrently or in threads.
    You should try to avoid doing expensive IO in teardowns, they are mean for error handling and cleaning up resources.

[global interpreter lock]: https://realpython.com/python-gil/
[Gunicorn]: https://gunicorn.org
[graphlib]: https://docs.python.org/3/library/graphlib.html
[graphlib2]: https://github.com/adriangb/graphlib2
[anyio TaskGroups]: https://anyio.readthedocs.io/en/stable/tasks.html
