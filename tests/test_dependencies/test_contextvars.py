from contextvars import ContextVar
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware

from xpresso import App, Depends, Operation, Path, Request, Response
from xpresso.middleware import Middleware
from xpresso.testclient import TestClient

legacy_request_state_context_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "legacy_request_state_context_var", default=None
)


async def set_up_request_state_dependency() -> AsyncIterator[Dict[str, Any]]:
    request_state = {"user": "deadpond"}
    contextvar_token = legacy_request_state_context_var.set(request_state)
    yield request_state
    legacy_request_state_context_var.reset(contextvar_token)


async def custom_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    response = await call_next(request)
    response.headers["custom"] = "foo"
    return response


def get_user():
    request_state = legacy_request_state_context_var.get()
    assert request_state
    return request_state["user"]


app = App(
    routes=[
        Path(
            "/user",
            get=Operation(
                get_user, dependencies=[Depends(set_up_request_state_dependency)]
            ),
        )
    ],
    middleware=[Middleware(BaseHTTPMiddleware, dispatch=custom_middleware)],
)


client = TestClient(app)


def test_dependency_contextvars():
    """
    Check that custom middlewares don't affect the contextvar context for dependencies.

    The code before yield and the code after yield should be run in the same contextvar
    context, so that request_state_context_var.reset(contextvar_token).

    If they are run in a different context, that raises an error.
    """
    response = client.get("/user")
    assert response.json() == "deadpond"
    assert response.headers["custom"] == "foo"
