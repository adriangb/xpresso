from typing import List

from pydantic import BaseModel

from xpresso import App, FromFormData, FromFormField, Path


class SearchForm(BaseModel):
    name: str  # implicit FromFormField[str]
    tags: FromFormField[List[str]]


async def log_search(form: FromFormData[SearchForm]) -> str:
    return f"{form.name} searched for {', '.join(form.tags)}"


app = App(routes=[Path(path="/form", post=log_search)])
