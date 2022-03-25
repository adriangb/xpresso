import typing
from io import BytesIO

import pytest
from pydantic import BaseModel
from starlette.responses import Response
from starlette.testclient import TestClient

from xpresso import App, Form, FormFile, FromFormFile, FromMultipart, Path, UploadFile
from xpresso.typing import Annotated

Files = typing.List[
    typing.Tuple[
        str,
        typing.Union[
            typing.Tuple[
                typing.Optional[str], typing.Union[bytes, typing.BinaryIO], str
            ],
            typing.Tuple[typing.Optional[str], typing.Union[bytes, typing.BinaryIO]],
        ],
    ]
]
Data = typing.List[typing.Tuple[str, str]]


class TruthyEmptyList(typing.List[typing.Any]):
    """Used to force multipart requests"""

    def __bool__(self) -> bool:
        return True


def test_uploadfile_field() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: FromFormFile[UploadFile]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert (await body.file.read()) == file_payload
        return Response()

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = [
        (
            "file",
            (
                "file.txt",
                BytesIO(file_payload),
            ),
        ),
    ]
    data: Data = []
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text

    expected_openapi: typing.Dict[str, typing.Any] = {
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
                            "multipart/form-data": {
                                "schema": {
                                    "required": ["file"],
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    },
                                },
                                "encoding": {"file": {}},
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_bytes_field() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: FromFormFile[bytes]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.file == file_payload
        return Response()

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = [
        (
            "file",
            (
                "file.txt",
                BytesIO(file_payload),
            ),
        ),
    ]
    data: Data = []
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text

    expected_openapi: typing.Dict[str, typing.Any] = {
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
                            "multipart/form-data": {
                                "schema": {
                                    "required": ["file"],
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"}
                                    },
                                },
                                "encoding": {"file": {}},
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_scalar_alias() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: Annotated[bytes, FormFile(alias="realFieldName")]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.file == file_payload
        return Response()

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = [
        (
            "realFieldName",
            (
                "file.txt",
                BytesIO(file_payload),
            ),
        ),
    ]
    data: Data = []
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text

    expected_openapi: typing.Dict[str, typing.Any] = {
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
                            "multipart/form-data": {
                                "schema": {
                                    "required": ["realFieldName"],
                                    "type": "object",
                                    "properties": {
                                        "realFieldName": {
                                            "type": "string",
                                            "format": "binary",
                                        }
                                    },
                                },
                                "encoding": {"realFieldName": {}},
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_array() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: FromFormFile[typing.List[bytes]]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.file == [file_payload, file_payload]
        return Response()

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = [
        (
            "file",
            (
                "file1.txt",
                file_payload,
            ),
        ),
        (
            "file",
            (
                "file2.txt",
                file_payload,
            ),
        ),
    ]
    data: Data = []
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text

    expected_openapi: typing.Dict[str, typing.Any] = {
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
                            "multipart/form-data": {
                                "schema": {
                                    "required": ["file"],
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "format": "binary",
                                            },
                                        }
                                    },
                                },
                                "encoding": {"file": {}},
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_array_alias() -> None:

    file_payload = b"abc"

    class FormDataModel(BaseModel):
        file: Annotated[typing.List[bytes], FormFile(alias="realFieldName")]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        assert body.file == [file_payload, file_payload]
        return Response()

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = [
        (
            "realFieldName",
            (
                "file1.txt",
                file_payload,
            ),
        ),
        (
            "realFieldName",
            (
                "file2.txt",
                file_payload,
            ),
        ),
    ]
    data: Data = []
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text

    expected_openapi: typing.Dict[str, typing.Any] = {
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
                            "multipart/form-data": {
                                "schema": {
                                    "required": ["realFieldName"],
                                    "type": "object",
                                    "properties": {
                                        "realFieldName": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "format": "binary",
                                            },
                                        }
                                    },
                                },
                                "encoding": {"realFieldName": {}},
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_string_instead_of_file() -> None:
    class FormDataModel(BaseModel):
        file: FromFormFile[bytes]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        ...

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = TruthyEmptyList()
    data: Data = [("file", "notafile")]
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 422, resp.text
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "file"],
                "msg": "Expected a file, got a string",
                "type": "type_error",
            }
        ]
    }


def test_missing_file():
    class FormDataModel(BaseModel):
        file: FromFormFile[bytes]

    async def test(body: FromMultipart[FormDataModel]) -> Response:
        ...

    app = App([Path("/", post=test)])
    client = TestClient(app)

    files: Files = TruthyEmptyList()
    data: Data = [("otherfield", "placeholder")]
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 422, resp.text
    assert resp.json() == {
        "detail": [
            {
                "loc": ["body", "file"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]
    }


@pytest.mark.parametrize(
    "files,expected_response",
    [
        (TruthyEmptyList(), None),
        (
            [
                (
                    "file",
                    (
                        "file.txt",
                        b"foo bar",
                    ),
                )
            ],
            "foo bar",
        ),
    ],
)
def test_file_not_required(
    files: Files,
    expected_response: typing.Any,
):
    class FormDataModel(BaseModel):
        file: FromFormFile[typing.Optional[bytes]] = None

    async def test(body: FromMultipart[FormDataModel]) -> typing.Optional[bytes]:
        return body.file

    app = App([Path("/", post=test)])
    client = TestClient(app)

    data: Data = [("otherfield", "placeholder to ensure a valid multipart body")]
    resp = client.post("/", files=files, data=data)
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_response


def test_form_include_in_schema() -> None:
    class FormDataModel(BaseModel):
        file: FromFormFile[bytes]

    async def test(
        body: Annotated[FormDataModel, Form(include_in_schema=False)]
    ) -> Response:
        ...

    app = App([Path("/", post=test)])
    client = TestClient(app)

    expected_openapi: typing.Dict[str, typing.Any] = {
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
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_file_field_unknown_type() -> None:
    class FormDataModel(BaseModel):
        file: FromFormFile[str]

    async def test(
        body: Annotated[FormDataModel, Form(include_in_schema=False)]
    ) -> Response:
        ...

    app = App([Path("/", post=test)])

    with pytest.raises(TypeError, match="Unknown file type str"):
        with TestClient(app):
            pass
