# Routing

XPresso has a simple routing system, based on Starlette's routing system and the OpenAPI spec.

There are 3 main concepts in XPresso's routing system:

- **Operation**: this is equivalent to an OpenAPI operation. An operation is a unique combination of an HTTP method and a path, and has a 1:1 relationship with endpoint functions. XPresso's `Operation` class is derived from a Starlette `BaseRoute`.
- **Path**: this is the equivalent of an OpenAPI PathItem. A Path can contain 1 Operation for each method (but does not have to). Paths are were you specify your actual path like `/items/{item_id}`. `Path` is derived from Starltte's `BaseRoute`.
- **Router**: this is a thing wrapper around Starlette's Router, with support for dependencies, some other niceties and some deprecations.

All of these are meant to work with Starlette.
You can for example use Starlette's `Mount` or `Host` within an XPresso `Router` and then include `Path`s and `Operation`s inside of that `Mount` or `Host` and everything will just work:

```python
--8<-- "docs_src/tutorial/routing.py"
```

!!! note
    The `Mount` and `Host` in `xpresso.routing` are just imported from `Starlette` as a convenience.
    They are completely unmodified.

See [Starlette's routing docs] for more general information on Starlette's routing system.

[Starlette's routing docs]: https://www.starlette.io/routing/
