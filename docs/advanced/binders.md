# Binders

One of the core principles of Xpresso is that the framework does not get any special treatment.
While it is not always possible (or worth it) to make everything customizable, by ensuring that we do not special case our own implementations we allow you, the developer, to have the ability to implement things that would otherwise have to be feature requests.
This way everyone wins: we have less features to mantain, less edge cases to test and you get to make Xpresso work for your use case.

Binders are a great example of this philosophy.
They are how Xpresso interally processes request bodies, forms and parameters (cookies, headers, etc.).
It is also how most of the OpenAPI documentation is generated.
In fact, all of `FromQuery`/`QueryParam(...)`, `FromMultipart`/`Multipart(...)` and others are just a particular implementation of a Binder.

In this tutorial we will dive in depth into Binders, and by the end of it we will have built a custom binder that parses MessagePack requests bodies into a Pydantic model.

!!! note "Note"
    Binders are inspired by [BlackSheep] and [ASP.NET Core].
    Integration into the dependency injection system is inspired by [FastAPI].

!!! warning "Experimental APIs"
    The APIs for Binders are considered experimental.
    We encourage exploration and experimentation, but can't promise long term stability.

## Architecture

First, a word on how Binders work.
Binders leverage the dependency injection system.
They are themselves dependencies that your endpoint function (or other dependencies) will depend on.
And then they themselves depend on the incoming `Request` object in the case of body extractors or `HTTPConnection` in the case of parameters.

Binders also have a dual purpose:

1. They extract data (**Extractor**)
1. They generate OpenAPI specs (**OpenAPIProvider**s)

Each one of these two functionalities has it's own protocol/interface that Binders must implement.

## Markers

Because the same binder object can be used with multiple parameters (think about how `FromJson` is an alias for `Annotated[..., Json()]`; the `Json()` object will be the same in everywhere `FromJson` is used) it cannot be modified in-place to record information from the parameter it is being bound to (think for example how `FromQuery` automatically gets the query parameter name from the the Python parameter name and the type to parse into from the type annotation).

To get around this issue, we have the concept of `Markers`.
Markers are usually just data containers that when bound to a Python parameter (an `inspect.Parameter` instance in fact) will produce a unique Extractor and OpenAPIProvider instance.

Since we already had two interfaces to implement (Extractor and OpenAPIProvider) and each one needs a Marker, typically we will be implementing **4 different protocols/interfaces for each Binder**:

1. `OpenAPI{Body,Parameter}Marker`
1. `OpenAPI{Body,Parameter}`
1. `{Body,Parameter}ExtractorMarker`
1. `{Body,Parameter}Extractor`

!!! tip "Tip"
    This is already a lot of information.
    Before trying to implement your own marker, you may want to look at the source code for `FromJson` to see how a Binder you are already familiar with is implemented.

## Custom Binders: MessagePack body

In this tutorial we will be implementing a custom binder that extracts [MessagePack] request bodies into Pydantic models.

Start by making a folder to organize your work and adding an `__init__.py` file.
We will be putting several Python files in this folder.

### Tests

Like any good TDD'er, we'll write some tests first.
This will also help you, the reader, understand what the expected outcome is.
First, we need to define an app.
Create a file called `tests.py` with the following contents:

```python
--8<-- "docs_src/advanced/binders/msgpack/tests.py"
```

At this point we would have just stubbed out the actual implementations (just `FromMsgPack` for now, something like `FromMsgPack = Annotated[T, "placeholder"]` would do).
So go ahead and create a file called `functions.py` and add a stub for `FromMsgPack`.

But if we run our tests (`pytest tests.py`) they fail.
So we need to actually cook up the implementations next.

### Extractor

We'll start with the extractors.
Make a file called `extractor.py` with the following contents:

```python
--8<-- "docs_src/advanced/binders/msgpack/extractor.py"
```

!!! tip "Tip"
    All of these base classes are `typing.Protocol` classes.
    This means you do not actually have to inherit from them directly to implement them.
    But it can be helpful to do so to get IDE autocompletion on method signatures as you implement them.

### OpenAPIProvider

This OpenAPIProvider will be somewhat anemic: there isn't much we can describe about MessagePack to OpenAPI other than the expected media type and that it will be binary data.
Make a file called `openapi.py` with the following contents:

```python
--8<-- "docs_src/advanced/binders/msgpack/openapi.py"
```

You may notice that there are several pointless methods here that could have all been stuck into `get_openapi()`.
These aren't strictly necessary here, but would be used if we tried to use this Binder as form field in a `multipart/form-data` request, so we are showing them to you just in case.

### Putting it all together

Now we just need some sugar so we can call a single function and have it wire all of this stuff up.
Open `functions.py`, remove your `FromMsgPack` stub and add:

```python
--8<-- "docs_src/advanced/binders/msgpack/functions.py"
```

You don't have to worry much about `BodyBinderMarker`.
It's just a helper class that takes care of the interaction with the dependency injection system.

### Run the tests

That's it!
Now you can run the tests (`pytest tests.py`) and they should pass!

[FastAPI]: https://fastapi.tiangolo.com
[BlackSheep]: https://github.com/Neoteroi/BlackSheep
[ASP.NET Core]: https://docs.microsoft.com/en-us/aspnet/core/mvc/models/model-binding?view=aspnetcore-6.0
[MessagePack]: https://msgpack.org/index.html
