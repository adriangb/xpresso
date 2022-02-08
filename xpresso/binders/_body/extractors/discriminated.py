import inspect
import sys
import typing
from dataclasses import dataclass

if sys.version_info < (3, 9):
    from typing_extensions import Annotated, get_args, get_origin
else:
    from typing import Annotated, get_origin, get_args

from di.typing import get_markers_from_parameter
from starlette.requests import Request

from xpresso.binders.api import BodyExtractor, BodyExtractorMarker
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.exceptions import HTTPException


@dataclass(frozen=True, eq=False)
class ContentTypeDiscriminatedExtractor(BodyExtractor):
    sub_body_extractors: typing.Iterable[BodyExtractor]

    async def extract_from_request(self, request: Request) -> typing.Any:
        media_type = request.headers.get("content-type", None)
        for sub_body_extractor in self.sub_body_extractors:
            if sub_body_extractor.matches_media_type(media_type):
                return await sub_body_extractor.extract_from_request(request)
        if media_type:
            raise HTTPException(
                status_code=415, detail=f"Media type {media_type} is not acceptable"
            )
        else:
            raise HTTPException(status_code=415, detail="Content-Type header missing")


@dataclass(frozen=True)
class ContentTypeDiscriminatedExtractorMarker(BodyExtractorMarker):
    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        sub_body_extractors: typing.List[BodyExtractor] = []

        annotation = param.annotation
        origin = get_origin(annotation)
        assert origin is Annotated
        annotation = next(iter(get_args(annotation)))
        origin = get_origin(annotation)
        if origin is not typing.Union:
            raise TypeError("Unioned bodies must be a Union of simple bodies")
        args = get_args(annotation)
        for arg in args:
            sub_body_param = inspect.Parameter(
                name=param.name,
                kind=param.kind,
                annotation=arg,
                default=param.default,
            )
            marker: typing.Optional[BodyBinderMarker] = None
            for param_marker in get_markers_from_parameter(sub_body_param):
                if isinstance(param_marker, BodyBinderMarker):
                    marker = param_marker
                    break
            if marker is None:
                raise TypeError(f"Type annotation is missing body marker: {arg}")
            sub_body_extractor = marker.extractor_marker
            provider = sub_body_extractor.register_parameter(sub_body_param)
            sub_body_extractors.append(provider)
        return ContentTypeDiscriminatedExtractor(
            sub_body_extractors=sub_body_extractors
        )
