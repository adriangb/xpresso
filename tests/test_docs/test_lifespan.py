from dataclasses import dataclass

from docs_src.advanced.lifespan import Config, app
from xpresso import Dependant
from xpresso.testclient import TestClient


def test_lifespan() -> None:

    called = False

    @dataclass
    class TracedConfig(Config):
        def __post_init__(self) -> None:
            nonlocal called
            called = True

    with app.container.register_by_type(
        Dependant(TracedConfig, scope="app"),
        Config,
    ):
        with TestClient(app):
            pass

    assert called is True
