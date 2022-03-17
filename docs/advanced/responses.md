# Documenting OpenAPI responses

So far we have mostly just let Xpresso _infer_ the response model from type annotation.
By default, Xpresso assumes the response is JSON serializable type and uses `"application/json"` with an HTTP 200 status code.

You can also declare other responses or override the default response's status code, media type or schema.

## Adding an error response

We can document a 404 response as follows:

```python
--8<-- "docs_src/advanced/responses/tutorial_001.py"
```

!!! warning Warning
    Notice that when you are returning a non-default status code, you **must** return an actual `Response`, not an arbitrary JSON serializable object.

## Adding media types to the default response

```python
--8<-- "docs_src/advanced/responses/tutorial_002.py"
```

!!! tip Tip
    We could have also specified the return type for the `200` status code via the `default_response_model` parameter to `Operation`.
    Either way, we had to specify it because our function returns `Any` (it could return `Union[dict, Response]`, the situation is the same) so Xpresso can't infer the right response model from type annotations.

## Changing the media type for the default response

```python
--8<-- "docs_src/advanced/responses/tutorial_003.py"
```

!!! warning Warning
    Just changing the media type does not change how the response gets encoded, so we also had to pass `response_encoder=None` to avoid encoding `bytes` as JSON!

## Changing the status code for the default response

```python
--8<-- "docs_src/advanced/responses/tutorial_004.py"
```

Changing the default response status code via `default_response_status_code` changes the runtime behavior of our application in addition to the OpenAPI documentation: our endpoint will now return HTTP 201 responses.

## Responses on Router and Path

You can also set responses on Router and Path, which will get merged into any responses defined for Operation.
Responses for Operation take precedence over those of Path, and Path takes precedence over Routers.
Status codes, media types and headers are merged.
Examples and response models are overridden.

```python
--8<-- "docs_src/advanced/responses/tutorial_004.py"
```
