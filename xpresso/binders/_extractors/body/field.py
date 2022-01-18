import inspect
import typing
from dataclasses import dataclass

from di.typing import get_markers_from_parameter
from starlette.datastructures import FormData

from xpresso._utils.typing import model_field_from_param
from xpresso.binders._extractors.api import BodyExtractor, BodyExtractorMarker
from xpresso.binders.dependants import BodyBinderMarker
from xpresso.typing import Some


@dataclass(frozen=True)
class FieldExtractorBase(BodyExtractor):
    name: str
    field_extractor: BodyExtractor


class FieldExtractor(FieldExtractorBase):
    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        if self.name not in form:
            return None
        return Some(
            await self.field_extractor.extract_from_field(
                form[self.name], loc=(*loc, self.name)
            )
        )

    # These are implemented to work around pecularities of hashing bound methods on Python 3.7
    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, __o: object) -> bool:
        return self is __o


class RepeatedFieldExtractor(FieldExtractorBase):
    async def extract_from_form(
        self, form: FormData, *, loc: typing.Iterable[typing.Union[int, str]]
    ) -> typing.Optional[Some[typing.Any]]:
        return Some(
            [
                await self.field_extractor.extract_from_field(
                    val, loc=(*loc, self.name)
                )
                for field_name, val in form.multi_items()
                if field_name == self.name
            ]
        )


@dataclass(frozen=True)
class FieldExtractorMarkerBase(BodyExtractorMarker):
    cls: typing.ClassVar[
        typing.Union[typing.Type[RepeatedFieldExtractor], typing.Type[FieldExtractor]]
    ]
    alias: typing.Optional[str]

    def register_parameter(self, param: inspect.Parameter) -> BodyExtractor:
        field = model_field_from_param(param)
        name = self.alias or field.alias

        field_marker: typing.Optional[BodyExtractorMarker] = None
        for marker in get_markers_from_parameter(param):
            if isinstance(marker, BodyBinderMarker):
                if marker.extractor_marker is not self:
                    # the outermost marker must be the field marker (us)
                    # so the first one that isn't us is the inner marker
                    field_marker = marker.extractor_marker
        if field_marker is None:
            raise TypeError(
                "No field marker found"
                "\n You must include a valid field marker using ExtractField[AsJson[...]]"
                " or Annotated[..., Json(), Field()]"
            )
        field_extractor = field_marker.register_parameter(param)

        return self.cls(name=name, field_extractor=field_extractor)


class FieldExtractorMarker(FieldExtractorMarkerBase):
    cls = FieldExtractor


class RepeatedFieldExtractorMarker(FieldExtractorMarkerBase):
    cls = RepeatedFieldExtractor
