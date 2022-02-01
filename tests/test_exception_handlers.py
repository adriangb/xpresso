from xpresso import App, HTTPException, Path, Request
from xpresso.responses import JSONResponse
from xpresso.testclient import TestClient


def test_override_base_error_handler() -> None:
    async def custom_server_error_from_exception(request: Request, exc: Exception):
        return JSONResponse(
            {"detail": "Custom Server Error from Exception"}, status_code=500
        )

    async def raise_exception() -> None:
        raise Exception

    async def custom_server_error_from_500(request: Request, exc: Exception):
        return JSONResponse(
            {"detail": "Custom Server Error from HTTPException(500)"}, status_code=500
        )

    async def raise_500() -> None:
        raise HTTPException(500)

    app = App(
        routes=[
            Path("/raise-exception", get=raise_exception),
            Path("/raise-500", get=raise_500),
        ],
        exception_handlers={
            Exception: custom_server_error_from_exception,
            500: custom_server_error_from_500,
        },
    )

    client = TestClient(app)

    resp = client.get("/raise-exception")
    assert resp.status_code == 500, resp.content
    assert resp.json() == {"detail": "Custom Server Error from Exception"}

    resp = client.get("/raise-500")
    assert resp.status_code == 500, resp.content
    assert resp.json() == {"detail": "Custom Server Error from HTTPException(500)"}
