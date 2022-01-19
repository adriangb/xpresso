import time

import httpx
import pytest

from docs_src.advanced.dependencies.tutorial_002 import app


@pytest.mark.anyio
async def test_get_slow_endpoint() -> None:
    # this test may be flakey because it is susceptible to ovehread
    # if it is, we should just ditch the timing part of it and only verify behavior
    async with httpx.AsyncClient(app=app, base_url="http://example.com") as client:
        start = time.time()
        resp = await client.get("/slow")
        stop = time.time()
        assert resp.status_code == 200, resp.content
        elapsed = stop - start
        assert elapsed < 0.2
