from typing import List

from pydantic import BaseModel

from xpresso import App, FormField, FromFormData, Path
from xpresso.typing import Annotated


class SearchForm(BaseModel):
    name: str  # implicit FromFormField[str]
    tags: Annotated[List[str], FormField(explode=False)]


async def log_search(form: FromFormData[SearchForm]) -> str:
    return f"{form.name} searched for {', '.join(form.tags)}"


app = App(routes=[Path(path="/form", post=log_search)])
