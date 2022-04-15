import asyncpg  # type: ignore[import]
import uvicorn  # type: ignore[import]

from xpresso import App


async def main() -> None:
    app = App()
    async with asyncpg.create_pool(...) as pool:  # type: ignore
        app.dependency_overrides[asyncpg.Pool] = lambda: pool
        server = uvicorn.Server(uvicorn.Config(app))
        await server.serve()
