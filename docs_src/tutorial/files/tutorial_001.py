from xpresso import App, FromFile, Path, UploadFile


async def count_bytes_in_file(file: FromFile[UploadFile]) -> int:
    return len(await file.read())


app = App(routes=[Path(path="/count-bytes", put=count_bytes_in_file)])
