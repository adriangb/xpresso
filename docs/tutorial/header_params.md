# Header Parameters

Header parameters are declared the same way as `Query` and `Path` parameters:

```python
--8<-- "docs_src/tutorial/header_params/tutorial_001.py"
```

## Underscore conversion

Headers names are usually composed of several words separated by hyphens (`"-"`).
But Python veriable names cannot contain hyphens.
Since XPresso automatically derives the header names from the parameter names, this creates a problem.
To get around this, XPresso automatically converts parameter name underscores (`"_"`) to hyphens (`"-"`).
This is controlled using the `convert_underscores` parameter to `HeaderParam(...)`:

```python
--8<-- "docs_src/tutorial/header_params/tutorial_002.py"
```

!!! tip "Tip"
    The import `from XPresso.typing import Annotated` is just a convenience import.
    All it does is import `Annotated` from `typing` if your Python version is >= 3.9 and [typing_extensions] otherwise.
    But if you are already using Python >= 3.9, you can just replace that with `from typing import Annotated`.

!!! warning "Warning"
    It is pretty uncommon to use headers with underscores.
    You should probably think twice about setting `convert_underscores=False` and test that it doesn't break your clients, proxies, etc.

## Repeated Headers

## Serialization and Parsing
