import inspect
import typing

from pydantic.fields import ModelField
from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request

from xpresso._utils.compat import get_args
from xpresso._utils.typing import Some, model_field_from_param
from xpresso.binders._body.extractors.body_field_validation import validate_body_field
from xpresso.binders._body.extractors.form_encoded_field import (
    FormEncodedFieldExtractorMarker,
)
from xpresso.binders._body.form_field import FormDataExtractor, FormFieldMarker
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders.api import BodyExtractor


class FormDataBodyExtractor:
    __slots__ = ("media_type_validator", "field", "field_extractors")

    def __init__(
        self,
        media_type_validator: MediaTypeValidator,
        field: ModelField,
        field_extractors: typing.Mapping[str, FormDataExtractor],
    ) -> None:
        self.media_type_validator = media_type_validator
        self.field = field
        self.field_extractors = field_extractors

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
            return validate_body_field(
                None,
                field=self.field,
                loc=("body",),
            )
        return validate_body_field(
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

    async def extract_from_field(
        self,
        field: typing.Union[str, UploadFile],
        *,
        loc: typing.Iterable[typing.Union[str, int]],
    ) -> typing.Any:
        raise NotImplementedError


class FormDataBodyExtractorMarker(typing.NamedTuple):
    enforce_media_type: bool
    media_type: str

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        form_data_field = model_field_from_param(param)

        field_extractors: typing.Dict[str, FormDataExtractor] = {}
        # use pydantic to get rid of outer annotated, optional, etc.
        # use pydantic to get rid of outer annotated, optional, etc.
        model = form_data_field.type_
        for field_param in inspect.signature(model).parameters.values():
            for m in get_args(field_param.annotation):
                if isinstance(m, FormFieldMarker):
                    field_extractor = m.extractor_marker.register_parameter(field_param)
                    break
            else:
                field_extractor = FormEncodedFieldExtractorMarker(
                    alias=None,
                    style="form",
                    explode=True,
                ).register_parameter(field_param)
            field_extractors[field_param.name] = field_extractor
        if self.enforce_media_type and self.media_type:
            media_type_validator = get_media_type_validator(self.media_type)
        else:
            media_type_validator = get_media_type_validator(None)
        return FormDataBodyExtractor(
            media_type_validator=media_type_validator,
            field_extractors=field_extractors,
            field=form_data_field,
        )
