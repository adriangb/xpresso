from xpresso import App, FromRawBody, Path


async def count_bytes_in_file(data: FromRawBody[bytes]) -> int:
    return len(data)


app = App(routes=[Path(path="/count-bytes", put=count_bytes_in_file)])
