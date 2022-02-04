# Lifespans

Xpresso supports lifespan context managers from [Starlette].
This is the only way to handle startup/shutdown; there are no startup/shutdown events in Xpresso.

The main difference vs. Starlette is that the lifespan context manager is allowed to depend on `"app"` scoped dependencies (see [Dependency Scopes]), including the `App` itself:

```python
--8<-- "docs_src/tutorial/lifespans/tutorial_001.py"
```

!!! tip Tip
    You don't need `app.state` or `request.state` in Xpresso.
    Instead, you can create you own strongly typed mutable or immutable state object and inject it into your lifespan and/or endpoints like in the example above.

## Router lifespans

Routers can also have lifespans, and these lifespans will be executed when the top level `App`'s lifespan executes:

```python hl_lines="18-21 32-40"
--8<-- "docs_src/tutorial/lifespans/tutorial_002.py"
```

!!! note Note
    Only Xpresso Routers and mounted Apps support multiple lifespans.
    Lifespans for arbitrary mounted ASGI apps (using `Mount`) will _not_ work.

[Starlette]: https://www.starlette.io/events/
[Dependency Scopes]: ../tutorial/dependencies/scopes.md
