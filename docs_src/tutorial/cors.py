from typing import List

from pydantic import BaseSettings
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from xpresso import App, Path


class AppConfig(BaseSettings):
    # load this from the enviroment so that it can
    # be different in dev / prod / local
    cors_allowed_origins: List[str]


async def main():
    return {"message": "Hello World"}


def create_app() -> App:
    config = AppConfig()
    cors_middleware = Middleware(
        CORSMiddleware,
        allow_origins=config.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return App(routes=[Path("/", get=main)], middleware=[cors_middleware])
