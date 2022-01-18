import inspect
import typing
from dataclasses import dataclass
from urllib.parse import unquote_plus

from di.typing import get_markers_from_parameter
from pydantic.fields import ModelField
from starlette.datastructures import FormData, Headers, UploadFile
from starlette.formparsers import FormParser
from starlette.requests import Request

from xpresso._utils.media_type_validator import MediaTypeValidator
from xpresso._utils.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._extractors.api import BodyExtractor, BodyExtractorMarker
from xpresso.binders._extractors.body.form_field import FormFieldBodyExtractorMarker
from xpresso.binders._extractors.validator import validate as validate_data
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.typing import Some


@dataclass(frozen=True)
class FormDataBodyExtractorBase(BodyExtractor):
    media_type_validator: MediaTypeValidator
    field: ModelField
    field_extractors: typing.Dict[str, BodyExtractor]

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract_from_request(self, request: Request) -> typing.Any:
        media_type = request.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        if (
            request.headers.get("Content-Length", None) == "0"
            and self.field.required is not True
        ):
            # this is the only way to know the body is empty
            return validate_data(
                None,
                field=self.field,
                loc=("body",),
            )
        return validate_data(
            Some(await self._extract(await request.form(), loc=("body",))),
            field=self.field,
            loc=("body",),
        )

    async def _extract(
        self, form: FormData, loc: typing.Iterable[typing.Union[str, int]]
    ) -> typing.Any:
        res: typing.Dict[str, typing.Any] = {}
        for param_name, extractor in self.field_extractors.items():
            extracted = await extractor.extract_from_form(form, loc=loc)
            if isinstance(extracted, Some):
                res[param_name] = extracted.value
        return res

    # These are implemented to work around pecularities of hashing bound methods on Python 3.7
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, __o: object) -> bool:
        return self is __o


class FormDataBodyExtractor(FormDataBodyExtractorBase):
    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Optional[Some[typing.Any]]:
        if isinstance(field, UploadFile):

            async def stream_gen() -> typing.AsyncGenerator[bytes, None]:
                yield await field.read()  # type: ignore # UploadFile always returns bytes
                yield b""

            stream = stream_gen()

            form = await FormParser(Headers(), stream=stream).parse()

        else:
            forms = field.split("&")
            items = typing.cast(
                typing.List[typing.Tuple[str, str]],
                [tuple(unquote_plus(f).split("=", maxsplit=1)) for f in forms],
            )
            form = FormData(items)  # type: ignore[arg-type]

        return await self._extract(form, loc=loc)


class MultipartBodyExtractor(FormDataBodyExtractorBase):
    pass


@dataclass(frozen=True)
class FormDataBodyExtractorMarkerBase(BodyExtractorMarker):
    enforce_media_type: bool
    media_type: typing.ClassVar[str]
    cls: typing.ClassVar[
        typing.Union[
            typing.Type[FormDataBodyExtractor], typing.Type[MultipartBodyExtractor]
        ]
    ]

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        formdata_field = model_field_from_param(param)

        field_extractors: typing.Dict[str, BodyExtractor] = {}
        # use pydantic to get rid of outer annotated, optional, etc.
        annotation = formdata_field.type_
        for param_name, field_param in inspect.signature(annotation).parameters.items():
            marker: typing.Optional[BodyBinderMarker] = None
            for param_marker in get_markers_from_parameter(field_param):
                if isinstance(param_marker, BodyBinderMarker):
                    marker = param_marker
                    break
            extractor_marker: BodyExtractorMarker
            if marker is None:
                # use the defaults
                extractor_marker = FormFieldBodyExtractorMarker(
                    alias=None,
                    style="form",
                    explode=True,
                )
            else:
                extractor_marker = marker.extractor_marker
            extractor = extractor_marker.register_parameter(field_param)
            field_extractors[param_name] = extractor
        if self.enforce_media_type and self.media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        return self.cls(
            media_type_validator=media_type_validator,
            field_extractors=field_extractors,
            field=formdata_field,
        )


@dataclass(frozen=True)
class FormDataBodyExtractorMarker(FormDataBodyExtractorMarkerBase):
    media_type = "application/x-www-form-urlencoded"
    cls = FormDataBodyExtractor


@dataclass(frozen=True)
class MultipartBodyExtractorMarker(FormDataBodyExtractorMarkerBase):
    media_type = "multipart/form-data"
    cls = MultipartBodyExtractor
