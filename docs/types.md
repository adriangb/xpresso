# Typing in Python

This documentation assumes that you are familiar with type annotations in Python.
If you are not, that is okay! There are a lot of excellent guides out there to get you started:

- [RealPython's Python Type Checking guide](https://realpython.com/python-type-checking/)
- [FastAPI's introduction to python types](https://fastapi.tiangolo.com/python-types/)

## Runtime types (reflection)

Most languages loose a lot of their type information at runtime.
This can range between complete loss of type information (like TypeScript) or only weak support for runtime reflection (Golang).

Python stands out for it's strong support for typing information at runtime (often called _reflection_). Because of Python's dynamic runtime behavior, it is possible to read types and modify the runtime behavior of the program.

## `Annotated` and parameter metadata

Python 3.9 (via [PEP 593]) introduced the `Annotated` typing construct.
Since it's release in Python 3.9, this construct has been backported to older Python versions via the [typing_extensions] package.
So it is available all the way back to Python 3.7.
Xpresso uses `Annotated` extensively since it provides a composable, cohesive and widely supported pattern for attaching metadata for function parameters and class field declarations that is available at runtime.

If you've used FastAPI, you may be used to declaring things like `param: str = Path(gt=0)`.
When FastAPI was first released, this was the only way to add runtime metadata to a parameter in Python.
But now there is a better way to do this!
In Xpresso this same declaration would look like `param: FromPath[str]` or `param: Annotated[str, Path()]` (the former is just syntactic sugar for the latter).
As you see more usages of `Annoated` you will get used to it.
But for now all you need to know is that `param: Annotated[str, Path()]` is pretty much equivalent to `param: str = Path()`.

One of the main advantages to using `Annotated` is composability: multiple tools/libraries can include metadata together without conflict. For example, we can included information for both Xpresso and Pydantic using `param: Annotated[str, Path(), Field(min_length=1)`.
This is in contrast to FastAPI where `Query()` and friends are actually subclasses of Pydantic's `Field()`, which couples the web framework to Pydantic and adds complexity into `Query()`, `Path()`, etc. that is not really related to them directly.
To see an example of this in action, head over to the [Path Parameters] section of our documentation.

[typing_extensions]: https://pypi.org/project/typing-extensions/
[PEP 593]: https://www.python.org/dev/peps/pep-0593/
[Path Parameters]: tutorial/path_params.md
