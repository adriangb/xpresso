import inspect
import typing

from di.typing import get_markers_from_annotation
from starlette.datastructures import FormData

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._body.form_field import SupportsXpressoFormDataFieldExtractor
from xpresso.binders.api import SupportsFieldExtractor as SupportsFieldExtractor
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.typing import Some


class _FieldExtractor(typing.NamedTuple):
    field_name: str
    field_extractor: SupportsFieldExtractor

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some]:
        if self.field_name not in form:
            return None
        return Some(
            await self.field_extractor.extract_from_field(
                form[self.field_name], loc=(*loc, self.field_name)
            )
        )


class _RepeatedFieldExtractor(typing.NamedTuple):
    field_name: str
    field_extractor: SupportsFieldExtractor

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some]:
        return Some(
            [
                await self.field_extractor.extract_from_field(
                    val, loc=(*loc, self.field_name)
                )
                for field_name, val in form.multi_items()
                if field_name == self.field_name
            ]
        )


class FieldExtractorMarker(typing.NamedTuple):
    alias: typing.Optional[str]
    repeated: bool

    def register_parameter(
        self, param: inspect.Parameter
    ) -> SupportsXpressoFormDataFieldExtractor:
        field = model_field_from_param(param)
        field_name = self.alias or field.alias
        marker = next(
            get_markers_from_annotation(param.annotation, BodyBinderMarker), None
        )
        if marker is None:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        if marker.field_extractor_marker is None:
            raise TypeError(f"The field {param.name} is not valid as a form field")
        field_extractor = marker.field_extractor_marker.register_parameter(param)
        if self.repeated:
            return _RepeatedFieldExtractor(
                field_name=field_name, field_extractor=field_extractor
            )
        else:
            return _FieldExtractor(
                field_name=field_name, field_extractor=field_extractor
            )
