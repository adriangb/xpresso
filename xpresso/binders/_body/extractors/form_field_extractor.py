import inspect
import typing

from di.typing import get_markers_from_parameter
from starlette.datastructures import FormData

from xpresso._utils.typing import Some, model_field_from_param
from xpresso.binders._body.form_field import FormDataExtractor
from xpresso.binders.api import BodyExtractor
from xpresso.binders.dependants import BodyBinderMarker


class FieldExtractorBase:
    __slots__ = ("field_name", "field_extractor")

    def __init__(
        self,
        field_name: str,
        field_extractor: BodyExtractor,
    ) -> None:
        self.field_name = field_name
        self.field_extractor = field_extractor


class FieldExtractor(FieldExtractorBase):
    __slots__ = ()

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        if self.field_name not in form:
            return None
        return Some(
            await self.field_extractor.extract_from_field(
                form[self.field_name], loc=(*loc, self.field_name)
            )
        )


class RepeatedFieldExtractor(FieldExtractorBase):
    __slots__ = ()

    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
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

    def register_parameter(self, param: inspect.Parameter) -> FormDataExtractor:
        field = model_field_from_param(param)
        field_name = self.alias or field.alias
        for marker in get_markers_from_parameter(param):
            if isinstance(marker, BodyBinderMarker):
                field_marker = marker
                break
        else:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        field_extractor = field_marker.extractor_marker.register_parameter(param)
        if self.repeated:
            return RepeatedFieldExtractor(
                field_name=field_name, field_extractor=field_extractor
            )
        else:
            return FieldExtractor(
                field_name=field_name, field_extractor=field_extractor
            )
