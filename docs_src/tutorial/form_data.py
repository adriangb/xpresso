from dataclasses import dataclass
from typing import List

from pydantic import BaseModel

from xpresso import (
    App,
    ExtractField,
    FromFormData,
    FromFormField,
    FromJson,
    Path,
)


class JsonModel(BaseModel):
    foo: str


@dataclass(frozen=True)
class FormDataModel:
    name: str  # implicit FromFormField[str]
    tags: FromFormField[List[str]]
    json_data: ExtractField[FromJson[JsonModel]]


async def compare_json_to_form(
    form: FromFormData[FormDataModel],
) -> bool:
    return form.json_data.foo in form.tags


app = App(routes=[Path(path="/form", post=compare_json_to_form)])
