
# Sync dependencies

The dependency injection system supports sync and async dependencies, and you can mix and match them however you like.
For example, we can load our client's `base_url` from the enviroment using [Pydantic's configuration management].

We start by declaring our `BaseSettings` model:

```python hl_lines="4 10-14"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```

!!! note "Note"
    You can override the default URL by setting the `HTTPBIN_URL` env var before running this tutorial.

Next we'll declare the dependency:

```python hl_lines="17-21"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```

!!! tip "Tip"
    The dependency injection system is often smart enough to "autowire" your dependencies.
    In cases like these, you would not need a wrapper function (`get_httpbin_config()`) or the explicit annotation (`Annotated[..., Dependant(...)]`).
    But in this case Pydantic's BaseSettings class cannot easily be introspected, so we need to tell the dependency injection system how to construct it.

Now we use this dependency in our exising dependendency:

```python hl_lines="24"
--8<-- "docs_src/tutorial/dependencies/tutorial_003.py"
```
