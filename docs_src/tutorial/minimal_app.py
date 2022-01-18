from xpresso import App, Path


async def endpoint():
    return {"message": "Hello World"}


app = App(routes=[Path(path="/", get=endpoint)])
