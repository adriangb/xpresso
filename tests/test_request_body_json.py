import typing

from pydantic import BaseModel
from starlette.testclient import TestClient

from xpresso import App, FromJson, Json, Path, Request, Response
from xpresso.typing import Annotated


class InnerModel(BaseModel):
    a: int
    b: str


class OuterModel(BaseModel):
    inner: InnerModel


inner_payload = {"a": 1, "b": "2"}
outer_payload = {"inner": inner_payload}


def test_pydantic() -> None:
    async def endpoint(model: FromJson[OuterModel]) -> Response:
        assert model == outer_payload
        return Response()

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/", json=outer_payload)
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
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OuterModel"}
                            }
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "InnerModel": {
                    "title": "InnerModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
                    },
                },
                "OuterModel": {
                    "title": "OuterModel",
                    "required": ["inner"],
                    "type": "object",
                    "properties": {
                        "inner": {"$ref": "#/components/schemas/InnerModel"}
                    },
                },
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


def test_builtin() -> None:
    async def endpoint(model: FromJson[typing.List[int]]) -> Response:
        assert model == [1, 2]
        return Response()

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/", json=[1, 2])
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
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "integer"},
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

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_non_nullable_not_required() -> None:

    default = OuterModel(inner=InnerModel(a=1, b="2"))

    async def endpoint(model: FromJson[OuterModel] = default) -> None:
        assert model == default

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/")
    assert resp.status_code == 200, resp.content

    resp = client.post("/", data=b"null", headers={"Content-Type": "application/json"})
    assert resp.status_code == 422, resp.content

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
                            "application/json": {
                                "schema": {
                                    "title": "Model",
                                    "allOf": [
                                        {"$ref": "#/components/schemas/OuterModel"}
                                    ],
                                    "default": {"inner": {"a": 1, "b": "2"}},
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
                "InnerModel": {
                    "title": "InnerModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
                    },
                },
                "OuterModel": {
                    "title": "OuterModel",
                    "required": ["inner"],
                    "type": "object",
                    "properties": {
                        "inner": {"$ref": "#/components/schemas/InnerModel"}
                    },
                },
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


def test_nullable_required() -> None:
    async def endpoint(model: FromJson[typing.Optional[OuterModel]]) -> None:
        ...

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/")
    assert resp.status_code == 422, resp.content

    resp = client.post("/", data=b"null", headers={"Content-Type": "application/json"})
    assert resp.status_code == 200, resp.content

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
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/OuterModel",
                                    "nullable": True,
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
                "InnerModel": {
                    "title": "InnerModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
                    },
                },
                "OuterModel": {
                    "title": "OuterModel",
                    "required": ["inner"],
                    "type": "object",
                    "properties": {
                        "inner": {"$ref": "#/components/schemas/InnerModel"}
                    },
                },
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


def test_nullable_not_required() -> None:
    async def endpoint(model: FromJson[typing.Optional[OuterModel]] = None) -> None:
        ...

    app = App([Path("/", post=endpoint)])
    client = TestClient(app)

    resp = client.post("/")
    assert resp.status_code == 200, resp.content

    resp = client.post("/", data=b"null", headers={"Content-Type": "application/json"})
    assert resp.status_code == 200, resp.content

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
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/OuterModel",
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
                "InnerModel": {
                    "title": "InnerModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
                    },
                },
                "OuterModel": {
                    "title": "OuterModel",
                    "required": ["inner"],
                    "type": "object",
                    "properties": {
                        "inner": {"$ref": "#/components/schemas/InnerModel"}
                    },
                },
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


def test_include_in_schema() -> None:
    async def endpoint(body: Annotated[str, Json(include_in_schema=False)]) -> None:
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
                            "content": {"application/json": {}},
                        }
                    }
                }
            }
        },
    }

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_invalid_json() -> None:
    async def endpoint(model: FromJson[OuterModel]) -> Response:
        raise AssertionError("Should not be called")  # pragma: no cover

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post(
            "/", data=b"notvalidjson", headers={"content-type": "application/json"}
        )
    assert resp.status_code == 422
    assert resp.json() == {
        "detail": [
            {"loc": ["body"], "msg": "Data is not valid JSON", "type": "type_error"}
        ]
    }


def test_consume() -> None:
    async def endpoint(
        body: Annotated[str, Json(consume=False)], request: Request
    ) -> None:
        assert f'"{body}"' == (await request.body()).decode()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post(
            "/", data=b'"test"', headers={"Content-Type": "application/json"}
        )
    assert resp.status_code == 200


def test_marker_used_in_multiple_locations():
    async def endpoint(
        model1: Annotated[OuterModel, Json(consume=True)],
        model2: Annotated[OuterModel, Json(consume=True)],
    ) -> Response:
        assert model1.dict() == model2.dict() == outer_payload
        return Response()

    app = App([Path("/", post=endpoint)])

    client = TestClient(app)
    resp = client.post("/", json=outer_payload)
    assert resp.status_code == 200, resp.content

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
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/OuterModel"}
                            }
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "InnerModel": {
                    "title": "InnerModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
                    },
                },
                "OuterModel": {
                    "title": "OuterModel",
                    "required": ["inner"],
                    "type": "object",
                    "properties": {
                        "inner": {"$ref": "#/components/schemas/InnerModel"}
                    },
                },
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


def test_media_type_validation_enabled() -> None:
    async def endpoint(
        value: Annotated[int, Json(enforce_media_type=True)]
    ) -> Response:
        assert value == 1
        return Response()

    app = App([Path("/", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post("/", data=b"1", headers={"Content-Type": "application/json"})
        assert resp.status_code == 200
        resp = client.post("/", data=b"1", headers={"Content-Type": "text/plain"})
        assert resp.status_code == 415
        assert "Media type text/plain is not supported" in resp.text


def test_media_type_validation_disabled() -> None:
    async def endpoint(
        value: Annotated[int, Json(enforce_media_type=False)]
    ) -> Response:
        assert value == 1
        return Response()

    app = App([Path("/validate-false", post=endpoint)])

    with TestClient(app) as client:
        resp = client.post(
            "/validate-false", data=b"1", headers={"Content-Type": "application/json"}
        )
        assert resp.status_code == 200
        resp = client.post(
            "/validate-false", data=b"1", headers={"Content-Type": "text/plain"}
        )
        assert resp.status_code == 200
