from pydantic import BaseModel


class User(BaseModel):
    foo: str
