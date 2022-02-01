from typing import Any, Dict

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from xpresso import App, Path, Request, Response, Router
from xpresso.routing.mount import Mount
from xpresso.testclient import TestClient


def test_router_middleware() -> None:
    async def endpoint() -> None:
        ...

    class AddCustomHeaderMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
        ) -> Response:
            resp = await call_next(request)
            resp.headers["X-Custom"] = "123"
            return resp

    app = App(
        routes=[
            Mount(
                "/with-middleware",
                app=Router(
                    routes=[
                        Path(
                            "/",
                            get=endpoint,
                        )
                    ],
                    middleware=[Middleware(AddCustomHeaderMiddleware)],
                ),
            ),
            Mount(
                "/without-middleware",
                app=Router(
                    routes=[
                        Path(
                            "/",
                            get=endpoint,
                        )
                    ]
                ),
            ),
        ]
    )

    client = TestClient(app)

    resp = client.get("/with-middleware/")
    assert resp.status_code == 200, resp.content
    assert resp.headers["X-Custom"] == "123"

    resp = client.get("/without-middleware/")
    assert resp.status_code == 200, resp.content
    assert "X-Custom" not in resp.headers


def test_router_middleware_modify_path() -> None:
    async def endpoint() -> None:
        ...

    class RerouteMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
        ) -> Response:
            request.scope["path"] = request.scope["path"].replace("bad", "good")
            return await call_next(request)

    app = App(
        routes=[
            Mount(
                "/",
                app=Router(
                    routes=[
                        Path(
                            "/good",
                            get=endpoint,
                        )
                    ],
                    middleware=[Middleware(RerouteMiddleware)],
                ),
            ),
        ]
    )

    client = TestClient(app)

    resp = client.get("/bad")
    assert resp.status_code == 200, resp.content

    resp = client.get("/very-bad")
    assert resp.status_code == 404, resp.content


def test_exclude_from_schema() -> None:
    app = App(
        routes=[
            Mount(
                "/mount",
                app=Router(
                    routes=[Path("/test", get=lambda: None)], include_in_schema=False
                ),
            )
        ]
    )

    expected_openapi_json: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {},
    }

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi_json
