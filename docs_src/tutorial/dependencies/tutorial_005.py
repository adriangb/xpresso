from pydantic import BaseModel

from xpresso import App, FromQuery, Path


class CurrentUser(BaseModel):
    username: FromQuery[str]


async def echo_user(user: CurrentUser) -> CurrentUser:
    return user


app = App(
    routes=[
        Path(
            "/echo/user",
            get=echo_user,
        )
    ]
)
