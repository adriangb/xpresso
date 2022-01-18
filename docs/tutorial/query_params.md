# Query parameters

Query parameters are the named parameters that come after the `?` in a URL:

```text
http://example.com/some/paths/?skip=1&limit=2
```

This URL has two simple query parameters:

- `skip`: value of `1`
- `limit`: value of `2`

In Xpresso, these are extracted using `FromQuery[...]`, which is an alias for `Annoated[..., QueryParam()]`.
Since they are part of the URL, they are always received as strings.
But just like with path parameters, Xpresso can extract them and parse them into Python types and data structrues:

```python
--8<-- "docs_src/tutorial/query_params/tutorial_001.py"
```

Now navigate to [http://127.0.0.1:8000/items/?skip=1&limit=1](http://127.0.0.1:8000/items/?skip=1&limit=1) to see the query parameters being used to filter items. You should get the following response:

```json
--8<-- "docs_src/tutorial/query_params/tutorial_001_response_1.json"
```

## Default (optional) parameters

Unlike path parameters which are _always_ required, query paramters can be optional.
To make a query parameter optional, simply give the parameter a default value like we do for `limit` and `skip`.
So, for our example above [http://localhost:8000/items/?skip=0&limit=2](http://localhost:8000/items/?skip=0&limit=2) and [http://localhost:8000/items/](http://localhost:8000/items/) will produce the same result:

```json
--8<-- "docs_src/tutorial/query_params/tutorial_001_response_2.json"
```

Of course if you _don't_ give the parameter a default value, it will be required and an error response will automatically be returned if it is missing. For example, given:

```python
--8<-- "docs_src/tutorial/query_params/tutorial_002.py"
```

If you navigate to [http://localhost:8000/math/double/](http://localhost:8000/math/double/) you will get:

```json
--8<-- "docs_src/tutorial/query_params/tutorial_002_response_1.json"
```

## Nullable parameters

Just because a parameter has a default value does not mean that it is _nullable_.
For example, `http://localhost:8000/items/?limit=` means that `limit` has a value of "", which is considered a `null` value by OpenAPI.
If you actually want to accept null values, you can make `None` an acceptable value for your parameter either using `Optional[...]` or `Union[..., None]`. On Python 3.10 you can also do `int | None`.

Now if a null value is sent, it will be converted to `None`.
It is even possible to have a nullable parameter with a non-null default value, for example to express "the default limit is 10, but you can request all items (no/null limit)":

```python
--8<-- "docs_src/tutorial/query_params/tutorial_003.py"
```

If you navigate to [http://localhost:8000/items/?limit=](http://localhost:8000/items/?limit=) you will get 3 items back:

```json
--8<-- "docs_src/tutorial/query_params/tutorial_003_response_1.json"
```

While not including the parameter ([http://localhost:8000/items/](http://localhost:8000/items/)) at all will give you the default (2):

```json
--8<-- "docs_src/tutorial/query_params/tutorial_003_response_2.json"
```

## Repeated query parameters

Query parameters can be repeated, for example `?param=1&param=2`.
You can extract these repeated query parmaeters into a Python list (`List[int]` in this case).
To accept repeated query parameters and extract them into a list, just pass the list type into `FromQuery[...]`:

```python
--8<-- "docs_src/tutorial/query_params/tutorial_004.py"
```

!!! warning "Warning"
    If no values are sent, you will get an empty list.
    To require at least one value, use parameter constraints, which you will learn about in the [Paramter Constraints and Metadata] section of the docs.

[PEP 613 type alias]: https://www.python.org/dev/peps/pep-0613/
[Paramter Constraints and Metadata]: param_constraints_and_metadata.md
