from typing import Any, TypeVar

from xpresso.binders.dependants import BinderMarker
from xpresso.typing import Annotated

from .extractor import ExtractorMarker
from .openapi import OpenAPIMarker

T = TypeVar("T")


def Json() -> Any:
    return BinderMarker(
        extractor_marker=ExtractorMarker(),
        openapi_marker=OpenAPIMarker(),
    )


FromJson = Annotated[T, Json()]
