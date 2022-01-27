# Dependency Caching

Xpresso has a dependency caching system.
This allows re-using of already computed dependencies within a request response cycle.
This is also what enables Xpresso to persist `"app"` scoped dependencies across requests (see [Scopes]).
By default, all dependencies are cached within their execution scope, but this can be disabled on a per-dependency basis with the `use_cache` argument to `Dependant`.

First we are going to declare a placeholder dependency with no sub-dependencies.
We are just going to compare instances, so there's nothing else needed in this dependency.

```python hl_lines="5-6"
--8<-- "docs_src/advanced/dependencies/tutorial_003.py"
```

Next we'll create two dependencies that depend on this dependency to test that sub-dependencies are shared:

```python hl_lines="9-10 13-14"
--8<-- "docs_src/advanced/dependencies/tutorial_003.py"
```

Finally we create an endpoint that checks that the shared sub-dependencies are the same but the dependency declared with `use_cache=False` is not the same:

```python hl_lines="17-25"
--8<-- "docs_src/advanced/dependencies/tutorial_003.py"
```

You can test this by running the app and navigating to [http://127.0.0.1:800/shared](http://127.0.0.1:800/shared).
You should get a `200 OK` response with no errors.

[Scopes]: ../../tutorial/dependencies/scopes.md
