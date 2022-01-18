# xpresso

[![codecov](https://codecov.io/gh/adriangb/xpresso/branch/main/graph/badge.svg?token=A0FXC8B93Y)](https://codecov.io/gh/adriangb/xpresso)
![Test & Release](https://github.com/adriangb/xpresso/actions/workflows/workflow.yaml/badge.svg)

## Introduction

xpresso is an ASGI web framework built on top of [Starlette], [Pydantic] and [di], with heavy inspiration from [FastAPI].

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
from typing import List, Optional
from pydantic import BaseModel
from xpresso import App, PathItem, FromPath, FromQuery

class UserModel(BaseModel):
    user_id: str
    age: Optional[int] = None

async def get_users(
    ids: FromPath[List[int]],
    include_age: FromQuery[bool],
) -> List[UserModel]:
    if include_age:
        return [UserModel(user_id=user_id, age=123) for user_id in ids]
    return [UserModel(user_id=user_id) for user_id in ids]

app = App(
    routes=[
        PathItem(
            path="/users/{ids}",
            get=get_users
        )
    ]
)
```

Run the application:

```shell
uvicorn example:app
```

For more examples, tutorials and reference materials, see our [documentation].

[Starlette]: https://github.com/encode/starlette
[Pydantic]: https://github.com/samuelcolvin/pydantic/
[FastAPI]: https://github.com/tiangolo/fastapi
[di]: https://github.com/adriangb/di
[Uvicorn]: http://www.uvicorn.org/
[documentation]: https://www.adriangb.com/xpresso/
