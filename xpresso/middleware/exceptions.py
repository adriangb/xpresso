import asyncio

from starlette.concurrency import run_in_threadpool
from starlette.exceptions import ExceptionMiddleware as StarletteExceptionMiddleware
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.types import Message, Receive, Scope, Send

from xpresso._utils.asgi import XpressoHTTPExtension


class ExceptionMiddleware(StarletteExceptionMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)  # type: ignore
            return

        response_started = False

        async def sender(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, sender)  # type: ignore
        except Exception as exc:
            handler = None

            if isinstance(exc, HTTPException):
                handler = self._status_handlers.get(exc.status_code)  # type: ignore

            if handler is None:
                handler = self._lookup_exception_handler(exc)  # type: ignore

            if handler is None:
                raise exc

            if response_started:
                msg = "Caught handled exception, but response already started."
                raise RuntimeError(msg) from exc

            request = Request(scope, receive=receive)
            if asyncio.iscoroutinefunction(handler):  # type: ignore
                response = await handler(request, exc)  # type: ignore
            else:
                response = await run_in_threadpool(handler, request, exc)  # type: ignore
            extension: XpressoHTTPExtension = scope["extensions"]["xpresso"]
            extension.response = response
            await response(scope, receive, sender)
            extension.response_sent = True
