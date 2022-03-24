from typing import Any, TypeVar

from xpresso.binders.dependants import BinderMarker
from xpresso.typing import Annotated

from .extractor import ExtractorMarker
from .openapi import OpenAPIMarker

T = TypeVar("T")


def MsgPack() -> Any:
    return BinderMarker(
        extractor_marker=ExtractorMarker(),
        openapi_marker=OpenAPIMarker(),
    )


FromMsgPack = Annotated[T, MsgPack()]
