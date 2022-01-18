from dataclasses import dataclass
from typing import List

from xpresso import App, FormEncodedField, FromFormData, Path
from xpresso.typing import Annotated


@dataclass(frozen=True)
class FormDataModel:
    tags: Annotated[List[str], FormEncodedField(style="spaceDelimited", explode=False)]


async def echo_tags(form: FromFormData[FormDataModel]) -> List[str]:
    return form.tags  # returned as JSON


app = App(routes=[Path(path="/echo-tags", post=echo_tags)])
