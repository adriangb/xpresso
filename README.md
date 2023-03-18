<p align="center">
  <a href="https://www.xpresso-api.dev"><img src="https://github.com/adriangb/xpresso/raw/main/docs/assets/images/xpresso-title.png" alt="Xpresso"></a>
</p>

<p align="center">
<a href="https://github.com/adriangb/xpresso/actions?query=workflow%3ACI%2FCD+event%3Apush+branch%3Amain" target="_blank">
    <img src="https://github.com/adriangb/xpresso/actions/workflows/workflow.yaml/badge.svg?event=push&branch=main" alt="Test">
</a>
<a href="https://codecov.io/gh/adriangb/xpresso" target="_blank">
    <img src="https://img.shields.io/codecov/c/github/adriangb/xpresso?color=%2334D058" alt="Coverage">
</a>
<a href="https://pypi.org/project/xpresso" target="_blank">
    <img src="https://img.shields.io/pypi/v/xpresso?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/xpresso" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/xpresso.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

Xpresso is an ASGI web framework built on top of [Starlette], [Pydantic] and [di], with heavy inspiration from [FastAPI].

Some of the standout features are:

- ASGI support for high performance (within the context of Python web frameworks)
- OpenAPI documentation generation
- Automatic parsing and validation of request bodies and parameters, with hooks for custom extractors
- Full support for [OpenAPI parameter serialization](https://swagger.io/docs/specification/serialization/)
- Highly typed and tested codebase with great IDE support
- A powerful dependency injection system, backed by [di]

## Requirements

Python 3.7+

## Installation

```shell
pip install xpresso
```

You'll also want to install an ASGI server, such as [Uvicorn].

```shell
pip install uvicorn
```

## Example

Create a file named `example.py`:

```python
from pydantic import BaseModel
from xpresso import App, Path, FromPath, FromQuery

class Item(BaseModel):
    item_id: int
    name: str

async def read_item(item_id: FromPath[int], name: FromQuery[str]) -> Item:
    return Item(item_id=item_id, name=name)

app = App(
    routes=[
        Path(
            "/items/{item_id}",
            get=read_item,
        )
    ]
)
```

Run the application:

```shell
uvicorn example:app
```

Navigate to [http://127.0.0.1:8000/items/123?name=foobarbaz](http://127.0.0.1:8000/items/123?name=foobarbaz) in your browser.
You will get the following JSON response:

```json
{"item_id":123,"name":"foobarbaz"}
```

Now navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to poke around the interactive [Swagger UI] documentation:

![Swagger UI](docs/readme_example_swagger.png)

For more examples, tutorials and reference materials, see our [documentation].

## Inspiration and relationship to other frameworks

Xpresso is mainly inspired by FastAPI.
FastAPI pioneered several ideas that are core to Xpresso's approach:

- Leverage Pydantic for JSON parsing, validation and schema generation.
- Leverage Starlette for routing and other low level web framework functionality.
- Provide a simple but powerful dependency injection system.
- Use that dependency injection system to provide extraction of request bodies, forms, query parameters, etc.

Xpresso takes these ideas and refines them by:

- Decoupling the dependency injection system from the request/response cycle, leading to an overall much more flexible and powerful dependency injection system, packaged up as the standalone [di] library.
- Decoupling the framework from Pydantic by using `Annotated` ([PEP 593]) instead of default values (`param: FromQuery[str]` instead of `param: str = Query(...)`).
- [Middleware on Routers] so that you can use generic ASGI middleware in a routing-aware manner (for example, installing profiling middleware on only some paths without using regex matching).
- Support for [lifespans on any Router or mounted App] (this silently fails in FastAPI and Starlette)
- [dependency injection into the application lifespan] and support for [multiple dependency scopes].
- Formalizing the framework for extracting parameters and bodies from requests into the [Binder API] so that 3rd party extensions can do anything the framework does.
- Support for [customizing parameter and form serialization].
- Better performance by implementing [dependency resolution in Rust], [executing dependencies concurrently] and [controlling threading of sync dependencies on a per-dependency basis].

### Inspiration **to** FastAPI

When I originally concieved Xpresso I wasn't sure what the goal was. I didn't necessarily want to replace FastAPI, I know how much work open source is and was not and am not willing to commit to something like that. So I always thought of the project more as a testing ground for interesting ideas for ASGI web frameworks in general and FastAPI in particular.

I am happy to report that in this sense it has been a _smash hit_. In the time since writing the above differences:
- Starlette added support for middleware on routers.
- The ASGI spec, Starlette and FastAPI added support for returning data from lifespans, which I think may be an even better idea than dependency scopes.
- FastAPI added support for PEP593 annotations, taking direct inspiration from Xpresso's approach.
- I've established a strong working relationship with Sebastián, FastAPI's author, and I foresee more ideas from Xpresso leaking into FastAPI in some way or another.

So where does that leave Xpresso? It's going to stay around, but it's less likely to become a stable production ready framework: it can provide more value to the community as an exprimental proving ground for ideas than as yet another "production ready" web framework.

[Starlette]: https://github.com/encode/starlette
[Pydantic]: https://github.com/samuelcolvin/pydantic/
[FastAPI]: https://github.com/adriangb/xpresso
[di]: https://github.com/adriangb/di
[Uvicorn]: http://www.uvicorn.org/
[documentation]: https://www.xpresso-api.dev/
[Swagger UI]: https://swagger.io/tools/swagger-ui/
[dependency injection into the application lifespan]: https://xpresso-api.dev/latest/tutorial/lifespan
[multiple dependency scopes]: https://xpresso-api.dev/latest/tutorial/dependencies/scopes/
[dependency resolution in Rust]: https://github.com/adriangb/graphlib2
[executing dependencies concurrently]: https://xpresso-api.dev/latest/advanced/dependencies/performance/#concurrent-execution
[controlling threading of sync dependencies on a per-dependency basis]: https://xpresso-api.dev/latest/advanced/dependencies/performance/#sync-vs-async
[PEP 593]: https://www.python.org/dev/peps/pep-0593/
[Binder API]: https://xpresso-api.dev/latest/advanced/binders/
[customizing parameter and form serialization]: https://xpresso-api.dev/latest/tutorial/query_params/#customizing-deserialization
[lifespans on any Router or mounted App]: https://xpresso-api.dev/latest/tutorial/lifespan/
[Middleware on Routers]: https://xpresso-api.dev/0.14.1/tutorial/middleware/#middleware-on-routers
