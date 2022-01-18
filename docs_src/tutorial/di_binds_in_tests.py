import sys
from typing import Any, List

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from xpresso import App, FromPath, Path
from xpresso.dependencies.models import Dependant
from xpresso.testclient import TestClient


class DatabaseProtocol(Protocol):
    def execute(self, query: str) -> Any:
        ...


# Declare our endpoints
async def delete_user(name: FromPath[str], db: DatabaseProtocol) -> None:
    db.execute(f"DELETE {name}")


app = App(routes=[Path("/users/{name}", delete=delete_user)])

# Implement a "test" database
class TestDatabase:
    def __init__(self) -> None:
        self.logger: List[str] = []

    def execute(self, query: str) -> Any:
        self.logger.append(query)


def example_test() -> None:
    db = TestDatabase()
    # In tests, we bind this "test" database
    with app.container.bind(Dependant(lambda: db), DatabaseProtocol):
        client = TestClient(app)

        client.delete("/users/john")

        assert db.logger == ["DELETE john"]
