from docs_src.advanced.background_tasks import Log, app
from xpresso.testclient import TestClient


def test_background_task_tutorial() -> None:
    log = Log()
    with app.dependency_overrides as overrides:
        overrides[Log] = lambda: log
        with TestClient(app) as client:
            resp = client.get("/")
            assert resp.status_code == 200, resp.content
            assert set(log) == {"app", "connection"}
