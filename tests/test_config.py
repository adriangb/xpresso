import os
from unittest.mock import patch

from xpresso import App, Path
from xpresso.config import Config
from xpresso.testclient import TestClient


def test_coonfig() -> None:
    class AppConfig(Config):
        foobarbaz: int

    async def endpoint(cfg: AppConfig) -> int:
        return id(cfg)

    app = App(routes=[Path("/", get=endpoint)])

    with patch.dict(os.environ, {"FOOBARBAZ": "123"}):
        with TestClient(app) as client:
            resp1 = client.get("/")
            assert resp1.status_code == 200, resp1.content
            resp2 = client.get("/")
            assert resp2.status_code == 200, resp2.content
            assert resp1.json() == resp2.json()
