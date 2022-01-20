from xpresso import App, Operation, Path, Router
from xpresso.routing import Mount


async def items() -> None:
    ...


path = Path("/items", get=Operation(items))

inner_mount = Mount(path="/mount-again", routes=[path])

router = Router(routes=[inner_mount])

outer_mount = Mount(path="/mount", app=router)

app = App(routes=[outer_mount])
