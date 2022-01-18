from docs_src.tutorial.di_lifespan import app
from xpresso.testclient import TestClient


def test_lifespan() -> None:
    with TestClient(app):
        pass
