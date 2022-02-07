# Dependency Overrides

We've already seen one way of telling the dependency injection system how to wire a dependency that it can't auto-wire in the form of [Markers].

There are however other situations where Markers may not be the answer.
For these situations, Xpresso offers **dependency overrides** which lets you dynamically bind a provider to a dependency.
When you override a dependency, you completely replace the original provider (if any) in Xpresso's directed acyclic graph of dependencies.
This means that any sub-dependencies of the original provider (if any) will not be executed.
This also means that the provider you are registering can itself have sub-dependencies.
Those will get treated just like any other dependency, all of the same rules apply.

As an example, let's look at how we might write a test for our ongoing `httpx.AsyncClient` examples.
Here is the example we had previously from the [Dependency Injection - Introduction] section:

```python
--8<-- "docs_src/tutorial/dependencies/tutorial_001.py"
```

We don't want to actually make network calls to HTTPBin in our tests, so we swap out the `httpx.AsyncClient` for one using `httpx.MockTransport`:

```python hl_lines="13-16"
--8<-- "tests/test_docs/tutorial/dependencies/test_tutorial_001.py"
```

!!! tip
    You can use `app.dependency_overrides` both as a context manager (like in the example above) and as a regular mapping-like object.
    If used as a context manager, the binding will be reversed when the context manager exits.
    Otherwise, the bind is permanent.
    You probably should use the context manager form in tests so that you don't leak state from one test to another.

!!! tip
    We use a lambda here to tell the dependency injection system what parameters to include.
    But remember that this lambda will be called every time the dependency is requested.
    You can also create an instance outside of the lambda function and return that if you want to use the same instance everywhere.
    In this particular test, it doesn't make a difference.

!!! note
    Xpresso's `app.dependency_overrides` is just a wrapper around the more advanced functionality offered in [di].
    The lowest level, but most powerful, interface is `Container.register_hook` (`app.container.register_hook`).
    See [di's provider binding docs] for more details.

You can also use this same mechanism to declare a dependency on an abstract interface (including `typing.Protocol` classes) and then register a concrete provider in some `create_production_app()` class.

[Markers]: ../../tutorial/dependencies/README.md#explicit-dependencies-with-markers
[Dependency Injection - Introduction]: ../../tutorial/dependencies/README.md
[di]: https://github.com/adriangb/di
[di's provider binding docs]: https://www.adriangb.com/di/latest/binds/
