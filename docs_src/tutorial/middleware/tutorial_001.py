from typing import Sequence

from pydantic import BaseModel, BaseSettings

from xpresso import App, Path, Router
from xpresso.middleware import Middleware
from xpresso.middleware.cors import CORSMiddleware
from xpresso.routing.mount import Mount


class AppHealth(BaseModel):
    okay: bool


async def healthcheck() -> AppHealth:
    return AppHealth(okay=True)


class Greeting(BaseModel):
    message: str


async def greet_user() -> Greeting:
    return Greeting(message="Hello!")


class AppConfig(BaseSettings):
    cors_origins: Sequence[str]


def create_app(config: AppConfig) -> App:
    v1_router = Router(
        routes=[Path("/landing", get=greet_user)],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
    )

    return App(
        routes=[
            Mount(
                "/v1",
                app=v1_router,
            ),
            Path(
                "/health",
                get=healthcheck,
            ),
        ],
    )


def create_production_app() -> App:
    config = AppConfig()  # loaded from env variables
    return create_app(config)


def create_debug_app() -> App:
    origins = ("http://localhost:8000", "http://localhost:5000")
    config = AppConfig(cors_origins=origins)
    return create_app(config)
