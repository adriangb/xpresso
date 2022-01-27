# Dependency Injection

Xpresso has a built in [Dependency Injection] system.
You do not need to know what Dependency Injection is or be an expert in design patterns to get started.

## Background

Let's look at a simple case of a function needing an HTTP client.
For this example, we'll use [httpx].

```python
import httpx

def make_request() -> int:
    client = httpx.Client(base_url="http://example.com/v1/")
    resp = client.get("/")
    return resp.status_code

print(make_request())
```

This example _does not_ use dependency injection because `httpx.Client` (the **dependency**) is created by the the **dependant** (`make_request()`).
The most basic form of dependency injection would be to "inject" an instance of `httpx.Client` into `make_request()`:

```python
import httpx

def make_request(client: httpx.Client) -> int:
    resp = client.get("/")
    return resp.status_code

client = httpx.Client(base_url="http://example.com/v1/")
print(make_request(client))
```

This already gives us a lot of flexibility:

- **Shared logic**: if `http://example.com/v1/` gets updated to `http://example.com/v2/`, we only have to change that in one place, and we don't have to change our tests.
- **Testability**: we can test `make_request()` with an `httpx.Client` instance using a [MockTransport].
- **Performance**: http clients like httpx and similar things like database clients tend to re-use connections. So you can get a large performance benefit from sharing the same client / connections across your application.

There are many more benefits to dependency injection, and you can go really deep into the topic if you'd like, but for now this is enough background.

## Dependency Injection in Xpresso

Xpresso's dependency injection API is modeled after [FastAPI].
It is implemented as a standalone package called [di].
The simplest form of dependency injection is requesting a dependency in your endpoint function.
For simple cases, all we need to do is add a type annotation:

```python hl_lines="6"
--8<-- "docs_src/tutorial/dependencies/tutorial_001.py"
```

If you run the app (make a file called `example.py`, copy the source code above and run `uvicorn example:app`) and navigate to [http://127.0.0.1:8000/echo/url](http://127.0.0.1:8000/echo/url) you will get the following as a response:

```json
"https://httpbin.org/get"
```

### What happened in the background?

The dependency injection system ([di]) auto-wired the dependency on `httpx.AsyncClient`.
This means that it recognized that our endpoint function needed an instance of that class and so it created that class and injected it.
This works well for simple cases (classes that do not have any dependencies or where all of the parameters are themselves resolvable by [di]) and when it works, it may be all you need!

## Explicit dependencies with markers

There are many situations in which you can't rely on auto-wiring.
For example, if the value is coming from a function.
In these cases, you need to use an explicit marker.
In this example, we'll use an explicit marker to customize the `base_url` option to `httpx.AsyncClient`.

First, we declare a dependency function.
This function will just create the client with customized parameters and return it.

```python hl_lines="7-8"
--8<-- "docs_src/tutorial/dependencies/tutorial_002.py"
```

Next, we'll create the **Marker** for our dependency.
This is what the dependency injection system will look for.
You can declare it in the endpoint function's signature, but often it is convenient to declare Markers as a type alias to avoid cluttering the function signature:

```python hl_lines="11"
--8<-- "docs_src/tutorial/dependencies/tutorial_002.py"
```

!!! tip "Tip"
    For simple cases like this, you can even use a lambda function: `Dependant(lambda: httpx.AsyncClient(...))`
    Just be concious of legibility!

Since we are now specifying the `base_url` when we construct the `httpx.AsyncClient`, we can just use `"/get"` as the URL in our endpoint function:

```python hl_lines="15"
--8<-- "docs_src/tutorial/dependencies/tutorial_002.py"
```

That's it!

Markers provide a powerful system for telling the dependency injection system how to create and manage your dependencies.
They control construction, concurrency, caching and wiring, which are all topics we will explore in future chapters.

[Dependency Injection]: https://en.wikipedia.org/wiki/Dependency_injection
[httpx]: https://www.python-httpx.org
[MockTransport]: https://www.python-httpx.org/advanced/#mock-transports
[FastAPI]: https://fastapi.tiangolo.com/tutorial/dependencies/
[di]: https://github.com/adriangb/di
