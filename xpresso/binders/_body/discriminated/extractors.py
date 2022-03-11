import inspect
import typing

from di.typing import get_markers_from_annotation
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request

from xpresso._utils.compat import Annotated, get_args, get_origin
from xpresso.binders.api import SupportsBodyExtractor
from xpresso.binders.dependants import BodyBinderMarker


class _BodyExtractor(typing.NamedTuple):
    sub_body_extractors: typing.Tuple[SupportsBodyExtractor, ...]

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        media_type = connection.headers.get("content-type", None)
        for sub_body_extractor in self.sub_body_extractors:
            if sub_body_extractor.matches_media_type(media_type):
                return await sub_body_extractor.extract(connection)
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


class BodyExtractorMarker(typing.NamedTuple):
    def register_parameter(self, param: inspect.Parameter) -> SupportsBodyExtractor:
        sub_body_extractors: typing.List[SupportsBodyExtractor] = []

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
            marker = next(
                get_markers_from_annotation(
                    sub_body_param.annotation, BodyBinderMarker
                ),
                None,
            )
            if marker is None:
                raise TypeError(f"Type annotation is missing body marker: {arg}")
            sub_body_extractors.append(
                marker.register_parameter(sub_body_param).extractor
            )
        return _BodyExtractor(sub_body_extractors=tuple(sub_body_extractors))
