from typing import Any, AsyncIterator, Dict, Generator, Optional

import pytest
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Path, RawBody, UploadFile
from xpresso.bodies import FromRawBody
from xpresso.typing import Annotated


@pytest.mark.parametrize("consume", [True, False])
def test_extract_into_bytes(consume: bool):
    async def endpoint(file: Annotated[bytes, RawBody(consume=consume)]) -> Response:
        assert file == b"data"
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=b"data")
    assert resp.status_code == 200, resp.content


@pytest.mark.parametrize("consume", [True, False])
def test_extract_into_uploadfile(consume: bool):
    async def endpoint(
        file: Annotated[UploadFile, RawBody(consume=consume)]
    ) -> Response:
        assert await file.read() == b"data"
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=b"data")
    assert resp.status_code == 200, resp.content


def test_extract_into_stream():
    async def endpoint(file: FromRawBody[AsyncIterator[bytes]]) -> Response:
        got = bytearray()
        async for chunk in file:
            got.extend(chunk)
        assert got == b"data"
        return Response()

    app = App([Path("/", post=endpoint)])

    def stream() -> Generator[bytes, None, None]:
        yield b"d"
        yield b"ata"

    client = TestClient(app)
    resp = client.post("/", content=stream())  # type: ignore
    assert resp.status_code == 200, resp.content


def test_read_into_stream():
    async def endpoint(
        file: Annotated[AsyncIterator[bytes], RawBody(consume=False)]
    ) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    with pytest.raises(ValueError, match="consume=False is not supported for streams"):
        with TestClient(app):
            pass


@pytest.mark.parametrize(
    "data",
    [
        None,
        b"",
    ],
)
@pytest.mark.parametrize("consume", [True, False])
def test_extract_into_bytes_empty_file(
    data: Optional[bytes],
    consume: bool,
):
    async def endpoint(
        file: Annotated[Optional[bytes], RawBody(consume=consume)] = None
    ) -> Response:
        assert file is None
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=data)  # type: ignore[arg-type]
    assert resp.status_code == 200, resp.content


@pytest.mark.parametrize(
    "data",
    [
        None,
        b"",
    ],
)
@pytest.mark.parametrize("consume", [True, False])
def test_extract_into_uploadfile_empty_file(
    data: Optional[bytes],
    consume: bool,
):
    async def endpoint(
        file: Annotated[Optional[UploadFile], RawBody(consume=consume)] = None
    ) -> Response:
        assert file is None
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=data)  # type: ignore[arg-type]
    assert resp.status_code == 200, resp.content


@pytest.mark.parametrize(
    "data",
    [
        None,
        b"",
    ],
)
def test_extract_into_stream_empty_file(
    data: Optional[bytes],
):
    async def endpoint(
        file: FromRawBody[Optional[AsyncIterator[bytes]]] = None,
    ) -> Response:
        assert file is None
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=data)  # type: ignore[arg-type]
    assert resp.status_code == 200, resp.content


def test_unknown_type():
    async def endpoint(file: FromRawBody[str]) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    with pytest.raises(TypeError, match="Target type str is not recognized"):
        with TestClient(app):
            pass


def test_marker_used_in_multiple_locations():
    async def endpoint(
        file1: Annotated[bytes, RawBody(consume=True)],
        file2: Annotated[bytes, RawBody(consume=True)],
    ) -> Response:
        assert file1 == file2 == b"data"
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", content=b"data")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "requestBody": {
                        "content": {
                            "*/*": {"schema": {"type": "string", "format": "binary"}}
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }
    resp = client.get("/openapi.json")
    assert resp.json() == expected_openapi


@pytest.mark.parametrize(
    "given_content_type,expected_content_type",
    [
        (None, "*/*"),
        ("text/plain", "text/plain"),
        ("text/*", "text/*"),
        ("text/plain,text/csv", "text/plain,text/csv"),
    ],
)
def test_openapi_content_type(
    given_content_type: Optional[str], expected_content_type: str
):
    async def endpoint(
        file: Annotated[bytes, RawBody(media_type=given_content_type)]
    ) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "requestBody": {
                        "content": {
                            expected_content_type: {
                                "schema": {"type": "string", "format": "binary"}
                            }
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }

    assert resp.json() == expected_openapi


def test_openapi_optional():
    async def endpoint(file: FromRawBody[Optional[bytes]] = None) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "requestBody": {
                        "content": {
                            "*/*": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary",
                                    "nullable": True,
                                }
                            }
                        },
                        "required": False,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }

    assert resp.json() == expected_openapi


def test_openapi_include_in_schema():
    async def endpoint(
        file: Annotated[bytes, RawBody(include_in_schema=False)]
    ) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            }
        },
    }

    assert resp.json() == expected_openapi


def test_openapi_format():
    async def endpoint(file: Annotated[bytes, RawBody(format="base64")]) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "requestBody": {
                        "content": {
                            "*/*": {
                                "schema": {
                                    "type": "string",
                                    "format": "base64",
                                }
                            }
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }

    assert resp.json() == expected_openapi


def test_openapi_description():
    async def endpoint(
        file: Annotated[bytes, RawBody(description="foo bar baz")]
    ) -> Response:
        ...

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                        },
                    },
                    "requestBody": {
                        "content": {
                            "*/*": {"schema": {"type": "string", "format": "binary"}}
                        },
                        "description": "foo bar baz",
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ValidationError": {
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "type": "object",
                    "properties": {
                        "loc": {
                            "title": "Location",
                            "type": "array",
                            "items": {
                                "oneOf": [{"type": "string"}, {"type": "integer"}]
                            },
                        },
                        "msg": {"title": "Message", "type": "string"},
                        "type": {"title": "Error Type", "type": "string"},
                    },
                },
                "HTTPValidationError": {
                    "title": "HTTPValidationError",
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Detail",
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                        }
                    },
                },
            }
        },
    }

    assert resp.json() == expected_openapi
