# Application Lifespan

Xpresso supports lifespan context managers from [Starlette].
This is the only way to handle startup/shutdown; there are no startup/shutdown events in Xpresso.

The main difference vs. Starlette is that the lifespan context manager is allowed to depend on `"app"` scoped dependencies (see [Dependency Scopes]):

```python hl_lines="16"
--8<-- "docs_src/advanced/lifespan.py"
```

[Starlette]: https://www.starlette.io/events/
[Dependency Scopes]: ../tutorial/dependencies/scopes.md
