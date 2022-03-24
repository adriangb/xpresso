import inspect
import sys
from typing import Any, NamedTuple, Type

if sys.version_info < (3, 8):
    from typing_extensions import get_args
else:
    from typing import get_args

import msgpack  # type: ignore[import]
from pydantic import BaseModel

from xpresso import Request
from xpresso.binders.api import SupportsExtractor
from xpresso.requests import HTTPConnection


class Extractor(NamedTuple):
    model: Type[BaseModel]

    async def extract(self, connection: HTTPConnection) -> Any:
        assert isinstance(connection, Request)
        data = await connection.body()
        deserialized_obj: Any = msgpack.unpackb(data)  # type: ignore[assignment]
        # You probably want more checks and validation here
        # For example, handling empty bodies
        # This is just a tutorial!
        return self.model.parse_obj(deserialized_obj)


class ExtractorMarker:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsExtractor:
        # get the first paramater to Annotated, which should be our actual type
        model = next(iter(get_args(param.annotation)))
        if not issubclass(model, BaseModel):
            # You may want more rigourous checks here
            # Or you may want to accept non-Pydantic models
            # We do the easiest thing here
            raise TypeError(
                "MessagePack model must be a Pydantic model"
            )
        return Extractor(model)
