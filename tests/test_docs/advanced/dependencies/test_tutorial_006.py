import pytest
from httpx import AsyncClient

from docs_src.advanced.dependencies.tutorial_006 import (
    create_app,
    test_add_word_endpoint,
)


def test_example_test() -> None:
    test_add_word_endpoint()


@pytest.mark.anyio
async def test_against_sqlite() -> None:
    app = create_app()
    async with AsyncClient(app=app, base_url="http://example.com") as client:
        resp = await client.post("/words/", json="foo")  # type: ignore
        assert resp.status_code == 200
        assert resp.json() == "foo"
