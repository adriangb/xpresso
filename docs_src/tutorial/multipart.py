from dataclasses import dataclass
from typing import List

from pydantic import BaseModel

from xpresso import (
    App,
    ExtractRepeatedField,
    FromFile,
    FromFormField,
    FromMultipart,
    Path,
    UploadFile,
)


class JsonModel(BaseModel):
    foo: str


@dataclass(frozen=True)
class FormDataModel:
    name: str  # implicit FromFormField[str]
    tags: FromFormField[List[str]]
    files: ExtractRepeatedField[FromFile[List[UploadFile]]]


class UserUploadMetadata(BaseModel):
    name: str
    tags: List[str]
    nbytes: int


async def upload_data(form: FromMultipart[FormDataModel]) -> UserUploadMetadata:
    nbytes = 0
    for file in form.files:
        nbytes += len(await file.read())
    return UserUploadMetadata(
        name=form.name,
        tags=form.tags,
        nbytes=nbytes,
    )


app = App(routes=[Path(path="/form", post=upload_data)])
