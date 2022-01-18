import inspect
import sys
from typing import Any, Iterable, Optional, Union

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from starlette.datastructures import FormData, UploadFile
from starlette.requests import HTTPConnection, Request

from xpresso.typing import Some


class BodyExtractor(Protocol):
    async def extract_from_request(self, request: Request) -> Any:
        """Extract from top level request"""
        raise NotImplementedError

    async def extract_from_form(
        self,
        form: FormData,
        *,
        loc: Iterable[Union[str, int]],
    ) -> Optional[Some[Any]]:
        """Extract from a form"""
        raise NotImplementedError

    async def extract_from_field(
        self,
        field: Union[str, UploadFile],
        *,
        loc: Iterable[Union[str, int]],
    ) -> Any:
        """Extract from a form field"""
        raise NotImplementedError

    def matches_media_type(self, media_type: Optional[str]) -> bool:
        """Check if this extractor can extract the given media type"""
        raise NotImplementedError


class BodyExtractorMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        """Hook to pull information from the Python parameter/field this body is attached to"""
        raise NotImplementedError


class ParameterExtractor(Protocol):
    def extract(self, connection: HTTPConnection) -> Any:
        raise NotImplementedError


class ParameterExtractorMarker(Protocol):
    def register_parameter(self, param: inspect.Parameter) -> ParameterExtractor:
        """Hook to pull information from the Python parameter/field this body is attached to"""
        raise NotImplementedError
