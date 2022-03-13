from xpresso import App, FromFile, Path


async def count_bytes_in_file(data: FromFile[bytes]) -> int:
    return len(data)


app = App(routes=[Path(path="/count-bytes", put=count_bytes_in_file)])
