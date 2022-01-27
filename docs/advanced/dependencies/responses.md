# Accessing Responses from Dependencies

Xpresso gives you the ability to access and even modify responses from within dependencies.
You will be able to:

- Get a reference to the response returned by the endpoint function
- Modify that response in place
- Replace that response with a completely different response object

This functionality is enabled through **response proxies**:

- `xpresso.responses.get_response(request: Request) -> Response`
- `xpresso.responses.set_response(request: Request, response: Response) -> None`

These functions can only be called from within the teardown of a dependency.
If called from anywhere else (inside the endpoint or in the setup of a context manager dependency) they will raise an exception.
Further, modifying the response or calling `set_response()` will only work from a dependency in the `"operation"` scope (otherwise the response has already been sent).

## Reading responses

Here is an example of a dependency that logs the status code for every response on a path:

```python hl_lines="19-30"
--8<-- "docs_src/advanced/dependencies/tutorial_004.py"
```

If your dependency has the `"connection"` scope (like in the example above) you will be able to get a copy of the request, but attempting to modify it or replace it will have no result since it was already sent to the client.
The main advantage of using the `"connection"` scope is reduced latency for the client.

## Writing responses

If you need to modify the response, use the `"operation"` scope.
Here's an example of a simple request/context tracing system:

```python hl_lines="17-30"
--8<-- "docs_src/advanced/dependencies/tutorial_005.py"
```
