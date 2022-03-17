import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from starlette.testclient import TestClient

from xpresso import App, ByContentType, File, FromJson, Path, UploadFile


def test_multiple_content_types():
    async def endpoint(
        body: ByContentType[
            typing.Union[
                Annotated[UploadFile, File(media_type="image/png,image/jpg")],
                Annotated[UploadFile, File(media_type="image/*")],
                Annotated[UploadFile, File(media_type="text/plain")],
                FromJson[typing.List[int]],
            ]
        ]
    ) -> str:
        ...

    app = App([Path("/", post=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"title": "Response", "type": "string"}
                                }
                            },
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
                            "image/png,image/jpg": {
                                "schema": {"type": "string", "format": "binary"}
                            },
                            "image/*": {
                                "schema": {"type": "string", "format": "binary"}
                            },
                            "text/plain": {
                                "schema": {"type": "string", "format": "binary"}
                            },
                            "application/json": {
                                "schema": {
                                    "title": "Body",
                                    "type": "array",
                                    "items": {"type": "integer"},
                                }
                            },
                        }
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_include_in_schema():
    async def endpoint(
        body: ByContentType[
            typing.Union[
                Annotated[UploadFile, File(media_type="image/png,image/jpg")],
                Annotated[
                    UploadFile, File(media_type="image/*", include_in_schema=False)
                ],
            ]
        ]
    ) -> str:
        ...

    app = App([Path("/", post=endpoint)])

    expected_openapi: typing.Dict[str, typing.Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"title": "Response", "type": "string"}
                                }
                            },
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
                            "image/png,image/jpg": {
                                "schema": {"type": "string", "format": "binary"}
                            },
                        }
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
