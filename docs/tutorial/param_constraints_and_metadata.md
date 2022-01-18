# Constraints and Metadata for Parameters

Query, Path, Header and Cookie parameters benefit from Pydantic's rich validation and schema generation.
You can attach extra validation and schema metadata using Pydantic's `Field()`.
For in depth information on the topic, see [Pydantic]'s docs.
But here is a quick example of how this can work in xpresso.
First, import `Field` from Pydantic and `Annotated`:

```py hl_lines="1 4"
--8<-- "docs_src/tutorial/param_constraints_and_metadata/tutorial_001.py"
```

!!! tip "Tip"
    The import `from xpresso.typing import Annotated` is just a convenience import.
    All it does is import `Annotated` from `typing` if your Python version is >= 3.9 and [typing_extensions] otherwise.
    But if you are already using Python >= 3.9, you can just replace that with `from typing import Annotated`.

Now use `Field()` inside of `Annotated[...]` to attach validation and schema customziation metadata to the `price` field:

```py hl_lines="11-20"
--8<-- "docs_src/tutorial/param_constraints_and_metadata/tutorial_001.py"
```

!!! note "Note"
    You'll notice that there is some overlap between the parameters to `QueryParam(...)` and `Field(...)`, for example `description`.
    This is just a convenience for you, the developer, so that you don't have to import `Field(...)` for the most common use cases.
    Whenever there is a duplicate parameter, the value in `QueryParam(...)` is preferred with a fallback to `Field(...)`'s value.

!!! tip "Tip"
    If you are adding a lot of metadata, it may be convenient to make a [PEP 613 type alias] at the module level.
    For example, you can do `Limit = Annotated[int, QueryParam(), Field(gt=0)]` and then use that like `limit: Limit` in your endpoint function.
    This is also useful if you are re-using the same parameter in multiple function signatures or even across modules.

Of course, you will get automatic validation of the `gt` constraints and the metadata will be reflected inthe  OpenAPI schema:

![Swagger UI](param_constraints_and_metadata_001.png)

[Pydantic]: https://pydantic-docs.helpmanual.io
