from typing import List

from fastapi import UploadFile
from pydantic import BaseModel

from xpresso import App, FromFormFile, FromMultipart, Path


class UploadForm(BaseModel):
    name: str  # implicit FromFormField[str]
    files: FromFormFile[List[UploadFile]]


async def log_search(form: FromMultipart[UploadForm]) -> str:
    data = [(await f.read()).decode() for f in form.files]
    return f"{form.name} uploaded {', '.join(data)}"


app = App(routes=[Path(path="/form", post=log_search)])
