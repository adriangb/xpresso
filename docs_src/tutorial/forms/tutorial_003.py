from typing import List

from pydantic import BaseModel

from xpresso import App, FromFormFile, FromMultipart, Path, UploadFile


class UploadForm(BaseModel):
    name: str  # implicit FromFormField[str]
    files: FromFormFile[List[UploadFile]]


async def log_search(form: FromMultipart[UploadForm]) -> str:
    data = [(await f.read()).decode() for f in form.files]
    return f"{form.name} uploaded {', '.join(data)}"


app = App(routes=[Path(path="/form", post=log_search)])
