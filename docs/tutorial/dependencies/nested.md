# Nested dependencies

Dependencies can have sub-dependencies, which in turn can have more sub-dependencies, creating a nested structure of dependencies.
Xpresso supports arbitrarily deep nesting of dependencies and will organize them so that each dependency only gets executed once all of its sub-dependencies have already been executed.

!!! tip "Tip"
    The technical term for this sort of structure is a [Directed Acyclic Graph] (DAG for short).
    But don't worry, you don't need to understand graph theory to use nested dependencies.

To build nested dependencies, just create a dependency that depends on another dependency.
Continuing with our example of `httpx.AsyncClient`, we can create a dependency that holds the configuration for the client, namely the `base_url` for HTTPBin.

We'll start by declaring a Pydantic model using [Pydantic's config management system]:

```python hl_lines="2 8-12"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```

`pydantic.BaseSettings` subclasses are actually a great example of things that cannot be auto-wired by the dependency injection system (in this case, it is for various technical reasons that are not relevant to this tutorial). But we can easily tell the dependency injection system to just build the class with no parameters by default:

```python hl_lines="16"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```

The last thing we need to do is add the dependency to `get_client()` and use the config inside of `get_client()`:

```python hl_lines="20-21"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```

Now the application will behave exactly the same as before except that you can override the URL used for HTTPBin with the `HTTPBIN_URL` environment variable. For example, try setting it `HTTPBIN_URL=http://httpbin.org` (`http` instead of `https`).

[Directed Acyclic Graph]: https://en.wikipedia.org/wiki/Directed_acyclic_graph
[Pydantic's config management system]: https://pydantic-docs.helpmanual.io/usage/settings/
