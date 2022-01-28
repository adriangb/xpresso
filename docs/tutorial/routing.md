# Routing

Xpresso has a simple routing system, based on Starlette's routing system and the OpenAPI spec.

There are 3 main concepts in Xpresso's routing system:

- **Operation**: this is equivalent to an OpenAPI operation. An operation is a unique combination of an HTTP method and a path, and has a 1:1 relationship with endpoint functions. Xpresso's `Operation` class is derived from a Starlette `BaseRoute`.
- **Path**: this is the equivalent of an OpenAPI PathItem. A Path can contain 1 Operation for each method (but does not have to). Paths are were you specify your actual path like `/items/{item_id}`. `Path` is derived from Starltte's `BaseRoute`.
- **Router**: this is a thing wrapper around Starlette's Router, with support for dependencies, some other niceties and some deprecations.

All of these are meant to work with Starlette.
You can for example use Starlette's `Mount` or `Host` within an Xpresso `Router` and then include `Path`s and `Operation`s inside of that `Mount` or `Host` and everything will just work:

```python
--8<-- "docs_src/tutorial/routing/tutorial_001.py"
```

!!! note
    The `Mount` and `Host` in `xpresso.routing` are just imported from `Starlette` as a convenience.
    They are completely unmodified.

See [Starlette's routing docs] for more general information on Starlette's routing system.

## Customizing OpenAPI schemas for Operation and Path

`Operation`, `Path` and `Router` let you customize their OpenAPI schema.
You can add descriptions, tags and detailed response information:

- Add tags via the `tags` parameter
- Exclude a specific Operation from the schema via the `include_in_schema` parameter
- Add a summary for the Operation via the `summary` parameter
- Add a description for the Operation via the `description` parameter (by default the endpoint function's docstring)
- Mark the operation as deprecated via the `deprecated` parameter
- Customize responses via the `responses` parameter

```python
--8<-- "docs_src/tutorial/routing/tutorial_002.py"
```

!!! note "Note"
    Tags accumulate, responses accumulate with Operation responses overwriting Path responses and Path responses overwriting Router responses.
    Servers on the other hand overwrite each other.
    That is, a `servers` array on an Operation will overwrite _all_ servers specified on the Path, Router or App.

[Starlette's routing docs]: https://www.starlette.io/routing/
