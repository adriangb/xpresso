from xpresso import App, Path
from xpresso.testclient import TestClient

expected_html = open("tests/test_openapi/expected_swagger_html.html").read()


def test_swagger_html_generation() -> None:
    async def endpoint() -> None:
        ...

    app = App([Path("/", get=endpoint)])
    client = TestClient(app)

    resp = client.get("/docs")

    assert resp.status_code == 200, resp.content
    assert resp.text == expected_html
