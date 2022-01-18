from typing import Any, TypeVar

from xpresso.binders.dependants import BodyBinderMarker
from xpresso.typing import Annotated

from .extractor import MsgPackBodyExtractorMarker
from .openapi import OpenAPIBodyMarkerMsgPack

T = TypeVar("T")


def MsgPack() -> Any:
    return BodyBinderMarker(
        extractor_marker=MsgPackBodyExtractorMarker(),
        openapi_marker=OpenAPIBodyMarkerMsgPack(),
    )


FromMsgPack = Annotated[T, MsgPack()]
