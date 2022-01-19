# Dependencies Shared at the Operation, Path and Route level

Sometimes you will have dependencies that are not used directly in your endpoint function but you still need executed.
For example, you may have a Security dependency that enforces access but does not return any meaningful value.

You may also want a dependency to apply to all of the operations of a Path, or even all of the Paths managed by a Router (including mounted routers).

For these use cases, Xpresso lets you add dependencies directly to the Operation, Path or Router.

As an example, let's create a very basic authorization system.
We'll have an array query parameter called `roles` that contains the roles the user making the request can act as.

!!! danger
    This is not a real authorization system.
    In a secure production setting, you would use something like OAuth2, not query parameters.

First we'll make a factory function that, given a set of roles, creates a function that enforces those roles and returns a 403 response if any are missing:

```python hl_lines="6-14"
--8<-- "docs_src/tutorial/dependencies/tutorial_007.py"
```

Next we'll declare a couple of endpoints, one to delete an item and one to get an item:

```python hl_lines="17-18 21-22"
--8<-- "docs_src/tutorial/dependencies/tutorial_007.py"
```

Finally, we create our App and add dependencies to the App, Path and Operations:

```python hl_lines="25-38"
--8<-- "docs_src/tutorial/dependencies/tutorial_007.py"
```

!!! note
    The `dependencies` parameter to `App` gets passed directly to `App.router`.
    The same parameter is available on `Router` itself.

Run this app (save the source code above to `example.py` and run it using `uvicorn example:app`) and navigate to [http://127.0.0.1:8000/items/foobar](http://127.0.0.1:8000/items/foobar) and you will get the following response:

```json
--8<-- "docs_src/tutorial/dependencies/tutorial_007_response_001.json"
```

So let's add the `"user"` role to our query string: [http://127.0.0.1:8000/items/foobar?roles=user](http://127.0.0.1:8000/items/foobar?roles=user).
Now we get a new error:

```json
--8<-- "docs_src/tutorial/dependencies/tutorial_007_response_002.json"
```

Adding the `"items-user"` role we can now "get" an item by navigating to [http://127.0.0.1:8000/items/foobar?roles=user,items-user](http://127.0.0.1:8000/items/foobar?roles=user,items-user)

```json
--8<-- "docs_src/tutorial/dependencies/tutorial_007_response_003.json"
```

## Middleware, error handlers and dependencies

Generally speaking anything you can do with middleware or error handlers you can also do with dependencies.
The main advantage of using the dependency injection system is that dependencies can be applied at multiple levels (like in the example above) while middleware can only apply to the entire application.
Middleware also applies to the entire application, so if you only want to profile or log certain routes it can be cumbersome and inefficient.
