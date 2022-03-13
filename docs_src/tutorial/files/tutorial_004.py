from xpresso import App, File, Path, UploadFile
from xpresso.typing import Annotated


async def count_image_bytes(
    file: Annotated[
        UploadFile,
        File(media_type="image/*", enforce_media_type=True),
    ]
) -> int:
    return len(await file.read())


app = App(routes=[Path(path="/count-bytes", put=count_image_bytes)])
