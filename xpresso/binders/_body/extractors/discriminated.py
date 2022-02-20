import inspect
import typing

from di.typing import get_markers_from_parameter
from starlette.datastructures import UploadFile
from starlette.requests import Request

from xpresso._utils.compat import Annotated, get_args, get_origin
from xpresso.binders.api import BodyExtractor
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.exceptions import HTTPException


class ContentTypeDiscriminatedExtractor:
    __slots__ = ("sub_body_extractors",)

    def __init__(
        self,
        sub_body_extractors: typing.Iterable[BodyExtractor],
    ) -> None:
        self.sub_body_extractors = sub_body_extractors

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

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        raise NotImplementedError

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        raise NotImplementedError


class ContentTypeDiscriminatedExtractorMarker(typing.NamedTuple):
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
