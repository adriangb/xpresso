# Controlling the composition root

In dependency injection technical jargon, the "composition root" is a single logical place (function, module, etc.) where all of your dependendencies are "composed" together and abstractions are bound to concrete implementations.

You can acheive this in Xpresso if your are willing to take some control of application initialization.

In many cases, this will let you cut out intermediary dependencies (e.g. a dependency to get a database connection or load a config from the environment): you can load your config, create your database connection and bind your repos/DAOs so that your application never has to know about a config or even what database backend it is using.

```python
--8<-- "docs_src/advanced/dependencies/tutorial_006.py"
```

Notice that we didn't have to add a verbose `Depends(...)` to our endpoint function since we are wiring `WordsRepo` up in our composition root.

This pattern also lends iteself natually to _depending on abstractions_: because you aren't forced to specify how `WordsRepo` should be built, it can be an abstract interface (`SupportsWordsRepo`, using `typing.Protocol` or `abc.ABC`), leaving you with a clean and testable endpoint handler that has no mention of the concrete implementation of `SupportsWordsRepo` that will be used at runtime

## Running an ASIG server programmatically

If you are running your ASGI server programmatically you have control of the event loop, allowing you to intialize arbitrarily complex dependencies (for example, a database connection that requires an async context manager).

This also has the side effect of making ASGI lifespans in redundant since you can do anything a lifespan can yourself before starting the ASGI server.

Here is an example of this pattern using Uvicorn

```python
--8<-- "docs_src/advanced/dependencies/tutorial_007.py"
```

There are many variations to this pattern, you should try different arrangements to find one that best fits your use case.
For example, you could:

- Splitting out your aggregate root into a `build_app()` function
- Mix this manual wiring in the aggregate root with use of `Depends()`
- Use Uvicorn's `--factory` CLI parameter or `uvicorn.run(..., factory=True)` if you'd like to wire up your dependencies in a composition root but don't need to take control of the event loop or need to run under Gunicorn.
