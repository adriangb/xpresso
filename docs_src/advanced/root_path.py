from xpresso import App, Path, Request


def read_main(request: Request) -> str:
    return f"Hello from {request.url_for('main')}"


app = App(
    routes=[
        Path("/app", get=read_main, name="main"),
    ],
    root_path="/v1/api",
)
