import inspect
import typing

from pydantic.fields import ModelField
from starlette.datastructures import FormData
from starlette.requests import HTTPConnection, Request

from xpresso._utils.compat import get_args
from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import (
    FormFieldMarker,
    SupportsXpressoFormDataFieldExtractor,
)
from xpresso.binders._body.forms.form_encoded_extractor import (
    FormEncodedFieldExtractorMarker,
)
from xpresso.binders._body.media_type_validator import MediaTypeValidator
from xpresso.binders._body.media_type_validator import (
    get_validator as get_media_type_validator,
)
from xpresso.binders._body.pydantic_field_validator import validate_body_field
from xpresso.binders.api import SupportsBodyExtractor
from xpresso.typing import Some


class _BodyExtractor:
    __slots__ = ("media_type_validator", "field", "field_extractors")

    def __init__(
        self,
        media_type_validator: MediaTypeValidator,
        field: ModelField,
        field_extractors: typing.Mapping[str, SupportsXpressoFormDataFieldExtractor],
    ) -> None:
        self.media_type_validator = media_type_validator
        self.field = field
        self.field_extractors = field_extractors

    def matches_media_type(self, media_type: typing.Optional[str]) -> bool:
        return self.media_type_validator.matches(media_type)

    async def extract(self, connection: HTTPConnection) -> typing.Any:
        assert isinstance(connection, Request)
        media_type = connection.headers.get("content-type", None)
        self.media_type_validator.validate(media_type, loc=("body",))
        if (
            connection.headers.get("Content-Length", None) == "0"
            and self.field.required is not True
        ):
            # this is the only way to know the body is empty
            return validate_body_field(
                None,
                field=self.field,
                loc=("body",),
            )
        return validate_body_field(
            Some(await self._extract(await connection.form(), loc=("body",))),
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


class BodyExtractorMarker(typing.NamedTuple):
    enforce_media_type: bool
    media_type: str

    def register_parameter(self, param: inspect.Parameter) -> SupportsBodyExtractor:
        form_data_field = model_field_from_param(param)

        field_extractors: typing.Dict[str, SupportsXpressoFormDataFieldExtractor] = {}
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
        return _BodyExtractor(
            media_type_validator=media_type_validator,
            field_extractors=field_extractors,
            field=form_data_field,
        )
