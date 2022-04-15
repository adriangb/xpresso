from xpresso import App, Operation, Path
from xpresso.testclient import TestClient


def test_docstrings() -> None:
    """Check that doctring indentation is correctly parsed out"""

    async def endpoint() -> None:
        """Lorem ipsum:

        1. Dolor
        2. Amet
        """

    app = App([Path("/", get=endpoint)])
    client = TestClient(app)

    resp = client.get("/openapi.json")

    assert resp.status_code == 200, resp.content
    assert (
        resp.json()["paths"]["/"]["get"]["description"]
        == "Lorem ipsum:\n\n1. Dolor\n2. Amet"
    )


def test_description_overrides_docstring() -> None:
    async def endpoint() -> None:
        """123"""

    app = App([Path("/", get=Operation(endpoint, description="456"))])
    client = TestClient(app)

    resp = client.get("/openapi.json")

    assert resp.status_code == 200, resp.content
    assert resp.json()["paths"]["/"]["get"]["description"] == "456"
