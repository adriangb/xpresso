<p align="center">
  <a href="https://www.xpresso-api.dev"><img src="https://www.xpresso-api.dev/xpresso-with-title.png" alt="Xpresso"></a>
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

## Introduction

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

[Starlette]: https://github.com/encode/starlette
[Pydantic]: https://github.com/samuelcolvin/pydantic/
[FastAPI]: https://github.com/adriangb/xpresso
[di]: https://github.com/adriangb/di
[Uvicorn]: http://www.uvicorn.org/
[documentation]: https://www.xpresso-api.dev/
[Swagger UI]: https://swagger.io/tools/swagger-ui/
