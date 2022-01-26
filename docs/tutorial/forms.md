# Forms

To extract forms in XPresso, you start by declaring a data structure to unpack the form into.
The fields of the datastructure correspond to the fields of the form data.
The datastructure can be almost anything, including dataclasses, pydantic models and regular Python classes.

```python
--8<-- "docs_src/tutorial/form_data.py"
```

This request extracts a `application/x-www-form-urlencoded` request into a `FormDataModel` object.

!!! note "Note"
    Form fields (`FromFormField`) are extracted from the form directly, but things like JSON or files need to be yanked out of a specific field before they are parsed/extracted.
    So for non form-native fields (anything except `FromFormField`) you need to wrap it in `ExtractField`.

## Form serialization

XPresso fully supports the [OpenAPI parameter serialization] standard.
You can customize how extraction ocurrs using the `style` and `explode` keyword arguments to `FormField()`:

```python
--8<-- "docs_src/tutorial/form_field_custom_style.py"
```

## Multipart requests

Multipart requests (`multipart/form-data`) can be parsed almost identically to `application/x-www-form-urlencoded`.
You can't upload mixed files and data in an `application/x-www-form-urlencoded` request, so you'll need to use a Multipart request.
Multipart requests even support multiple files:

```python
--8<-- "docs_src/tutorial/multipart.py"
```

!!! note "Note"
    Fields in a `application/x-www-form-urlencoded` or `multipart/form-data` request can be repeated.
    This just means that a field of the same name appears more than once in the request.
    Often this is used to upload multiple files, such as in the example above.
    To declare repeated fields we need to do two things:
    1. Use `ExtractRepeatedField` instead of `ExtractField`.
    1. Make sure our type is actually a List/Tuple/Set (any sequence will do).

[openapi parameter serialization]: https://swagger.io/docs/specification/serialization/
