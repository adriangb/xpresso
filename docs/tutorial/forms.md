# Forms

To extract forms in Xpresso, you start by declaring a Pydantic model to unpack the form into.
The fields of the model correspond to the fields of the form data.

```python
--8<-- "docs_src/tutorial/forms/tutorial_001.py"
```

This request extracts a `application/x-www-form-urlencoded` request into a `FormModel` object.

## Form serialization

Xpresso fully supports the [OpenAPI parameter serialization] standard.
You can customize deserialization using the `style` and `explode` keyword arguments to `FormField()`:

```python
--8<-- "docs_src/tutorial/forms/tutorial_002.py"
```

## Multipart requests

Multipart requests (`multipart/form-data`) can be parsed almost identically to `application/x-www-form-urlencoded`.
You can't upload mixed files and data in an `application/x-www-form-urlencoded` request, so you'll need to use a Multipart request.
Multipart requests even support multiple files:

```python
--8<-- "docs_src/tutorial/forms/tutorial_003.py"
```

!!! tip "Tip"
    Fields in a `application/x-www-form-urlencoded` or `multipart/form-data` request can be repeated.
    This just means that a field of the same name appears more than once in the request.
    Often this is used to upload multiple files, such as in the example above.

[openapi parameter serialization]: https://swagger.io/docs/specification/serialization/
