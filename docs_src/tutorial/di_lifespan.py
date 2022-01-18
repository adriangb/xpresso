from xpresso import App


class DatabaseConnection:
    pass


async def lifespan(connection: DatabaseConnection):
    assert isinstance(connection, DatabaseConnection)


app = App(lifespan=lifespan)
