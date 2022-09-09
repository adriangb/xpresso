
# Scopes

In our last tutorial with `httpx.AsyncClient` we left off at [dependency lifecycles].
As you may have noticed, we are creating and tearing down the `httpx.AsyncClient` instance for each incoming request.
This is very inefficient!
Really what we want to do is create the `httpx.AsyncClient` once, when our application starts up, and then use the same instance for each request, only tearing down the client when our app shuts down.

To achieve this, we need to introduce **scopes**.
Scopes let you control the "lifetime" of your dependency and are inspired by [pytest]'s fixture system.
In Pytest you may have used scopes like "session", "module" or "function".
In Xpresso there are three scopes available:

1. `"endpoint"`: the dependency is created right before calling the endpoint function and torn down right after your function returns, but before the response is sent to the client.
1. `"connection"` (default): this scope is entered before the endpoint scope and before calling your endpoint function and is torn down right after the response is sent to the client.
1. `"app"`: the outermost scope. Dependencies in this scope are tied to the [lifespan] of the application.

So for our use case, we'll be wanting to use the `"app"` scope for `httpx.AsyncClient`:

```python hl_lines="19 31"
--8<-- "docs_src/tutorial/dependencies/tutorial_006.py"
```

Everything else can stay the same, this is all we need!

If you run this and navigate to [http://127.0.0.1:8000/echo/url](http://127.0.0.1:8000/echo/url) the response will be the same, but you will probably notice reduced latency if you refresh to make several requests.

## Scope inference

In Pytest a `"session"` scoped fixture can't depend on a `"function"` scoped fixture, and in Xpresso an `"app"` scoped fixture can't depend on an `"endpoint"` scoped fixture.

Unlike Pytest which forces you to hardcode all of the scopes, Xpresso is able to infer scopes from the dependency graph.
So in this case it says "oh, I see that `get_client` depends on `HttpBinConfig` and `HttpBinConfig` was not explicitly assigned a scope; I'll give `HttpBinConfig` and `"app"` scope then so that it is compatible with `get_client`".

[pytest]: https://docs.pytest.org/en/6.2.x/fixture.html
[dependency lifecycles]: lifecycle.md
