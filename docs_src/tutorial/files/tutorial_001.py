from xpresso import App, FromRawBody, Path, UploadFile


async def count_bytes_in_file(file: FromRawBody[UploadFile]) -> int:
    return len(await file.read())


app = App(routes=[Path(path="/count-bytes", put=count_bytes_in_file)])
