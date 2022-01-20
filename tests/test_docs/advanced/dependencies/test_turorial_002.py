import time

import httpx
import pytest

from docs_src.advanced.dependencies.tutorial_002 import app


@pytest.mark.anyio
@pytest.mark.slow
async def test_get_slow_endpoint() -> None:
    # unforuntely it is pretty hard to actually time this in tests without making
    # really slow tests just for the sake of running timing on them
    async with httpx.AsyncClient(app=app, base_url="http://example.com") as client:
        start = time.time()
        resp = await client.get("/slow")
        stop = time.time()
        assert resp.status_code == 200, resp.content
        elapsed = stop - start
        assert elapsed < 2
