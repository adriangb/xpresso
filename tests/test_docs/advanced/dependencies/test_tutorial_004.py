from docs_src.advanced.dependencies.tutorial_004 import StatusCodeLogFile, app
from xpresso.testclient import TestClient


def test_read_items_logging() -> None:
    log = StatusCodeLogFile()
    with app.dependency_overrides as overrides:
        overrides[StatusCodeLogFile] = lambda: log
        client = TestClient(app)

        resp = client.get("/items/foo")
        assert resp.status_code == 200, resp.content
        assert log == [200]

        resp = client.get("/items/baz")
        assert resp.status_code == 404, resp.content
        assert log == [200, 404]

        resp = client.get("/items/bar")
        assert resp.status_code == 200, resp.content
        assert log == [200, 404, 200]
