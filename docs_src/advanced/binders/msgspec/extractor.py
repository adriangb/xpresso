import inspect
import sys
from typing import Any, NamedTuple

if sys.version_info < (3, 8):
    from typing_extensions import get_args
else:
    from typing import get_args

import msgspec

from xpresso import Request
from xpresso.binders.api import SupportsExtractor
from xpresso.requests import HTTPConnection


class Extractor(NamedTuple):
    decoder: "msgspec.json.Decoder[Any]"

    async def extract(self, connection: HTTPConnection) -> Any:
        assert isinstance(connection, Request)
        data = await connection.body()
        return self.decoder.decode(data)


class ExtractorMarker:
    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsExtractor:
        # get the first parameter to Annotated, which should be our actual type
        model = next(iter(get_args(param.annotation)))
        return Extractor(msgspec.json.Decoder(model))
