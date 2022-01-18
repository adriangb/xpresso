import sys
from typing import Any

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from xpresso import App, FromPath, Path
from xpresso.dependencies.models import Dependant


class DatabaseProtocol(Protocol):
    def execute(self, query: str) -> Any:
        ...


# Declare our endpoints
async def delete_user(name: FromPath[str], db: DatabaseProtocol) -> None:
    db.execute(f"DELETE {name}")


app = App(routes=[Path("/users/{name}", delete=delete_user)])

# Implement a "real" database
class RealDatabase:
    def execute(self, query: str) -> Any:
        print(query)  # or some real databse stuff


# In production, we bind this "real" database
app.container.bind(Dependant(RealDatabase), DatabaseProtocol)
