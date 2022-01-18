# Dependency Injection

Xpresso has a powerful dependency injection system, backed by [di].
You can inject classes, callable class instances, sync and async functions and context managers.
These can be chained, and dependencies are auto wired.

In this example, we'll create a common set of query parameters that can be collected and used from multiple endpoints.

```python
--8<-- "docs_src/tutorial/di_basic.py"
```

You are encouraged to run this example by copying it to a `main.py` file and running it with `uvicorn main:app`.
As always, you can head over to [http://localhost:8000/docs](http://localhost:8000/docs) to see the live docs.

As it turns out, `FromQuery` is just a dependency that extracts a query paratemeter from the request, parses it into the type declared via the type annotation and then injects it into the function.
So really, we are alaready using nested dependencies!
Xpresso supports arbitrarily deep nested dependency graphs.

## Depending on abstractions

Binds can be used to depend on an abstract interface and inject an implementation at the main entrypoint.

```python
--8<-- "docs_src/tutorial/di_bind_abstractions.py"
```

## Substituting dependencies in tests

Let's write a small test for the example above:

```python
--8<-- "docs_src/tutorial/di_binds_in_tests.py"
```

Here we use `bind()` as a context manager to make sure this tests's state does not leak into other tests.

## Lifespan dependencies

You can use dependencies in lifespan events, and also cache these dependencies for endpoints:

```python
--8<-- "docs_src/tutorial/di_lifespan.py"
```

## App scoped dependencies

Dependencies can belong to the `"endpoint"` scope (the default), the `"connection"` scope (available after the endpoint has executed up until the response is sent; can be used to log responses for example) or the `"app"` scope (bound to the lifespan events of the application).

```python
--8<-- "docs_src/tutorial/di_app_scoped.py"
```

[di]: https://github.com/adriangb/di
