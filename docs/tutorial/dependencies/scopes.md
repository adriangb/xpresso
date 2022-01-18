
# Scopes

The dependency injection system in Xpresso supports a concept called "scopes".
Scopes let you specify the "lifetime" of your dependency and are inspired by [pytest]'s fixture system.
In this case, we probably don't want to create a new `httpx.AsyncClient` for each request, so let's move our dependency to the `"app"` scope:

```python hl_lines="14"
--8<-- "docs_src/tutorial/dependencies/tutorial_002.py"
```

If you run this and navigate to [http://127.0.0.1:8000/echo/headers](http://127.0.0.1:8000/echo/headers) the response will be the same, but you will probably notice reduced latency if you refresh to make several requests.

There are three scopes available:

1. `"endpoint"` (default): the dependency is created right before calling the path function and torn down right after your function returns, but before the response is sent to the client.
1. `"connection"`: this scope is entered before the endpoint scope and before calling your path function and is torn down right after the response is sent to the client.
1. `"app"`: the outermost scope. Dependencies in this scope are tied to the [lifespan] of the applicaion.

Just like in Pytest, dependencies in the `"endpoint"` scope can depend on dependencies in the `"app"` scope, but not the other way around.

!!! tip "Tip"
    Since the `"endpoint"` scope is torn down before the response is sent to the client you can modify or replace the response from the endpoint function here.
    On the other hand, the `"connection"` scope can access the response but modifying it will have no effect since the response has already been sent.
    Attempting to access the response from within the `"app"` scope will result in an error.
    More on this in the section on [working with responses from within dependencies] section.
