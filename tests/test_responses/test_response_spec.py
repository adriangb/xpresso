from typing import Any, Dict, List, Tuple, Union

from pydantic import BaseModel

from xpresso import App, Operation, Path
from xpresso.responses import FileResponse, JSONResponse, ResponseSpec
from xpresso.testclient import TestClient


def test_default_response_spec_merge_with_top_level_parameters() -> None:
    async def endpoint() -> None:
        ...

    app = App(
        routes=[
            Path(
                "/",
                post=Operation(
                    endpoint,
                    response_status_code=201,
                    responses={201: ResponseSpec(description="Item created")},
                ),
            )
        ]
    )

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "post": {
                    "responses": {
                        "201": {
                            "description": "Item created",
                            "content": {
                                "application/json": {},
                            },
                        }
                    }
                }
            }
        },
    }

    client = TestClient(app)

    resp = client.post("/")
    assert resp.status_code == 201, resp.content

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_default_response_spec_response_model_inferred() -> None:
    def returns_builtin() -> List[str]:
        ...

    def no_return():
        ...

    def returns_none() -> None:
        ...

    def returns_response() -> JSONResponse:
        ...

    def returns_response_union() -> Union[str, FileResponse]:
        ...

    def returns_model_union() -> Union[str, int]:
        ...

    class Model(BaseModel):
        foo: int

    def returns_pydantic_model() -> Model:
        ...

    app = App(
        routes=[
            Path(
                "/returns_builtin",
                get=returns_builtin,
            ),
            Path(
                "/returns_builtin-overriden",
                get=Operation(returns_builtin, response_model=Tuple[str, str]),
            ),
            Path(
                "/no_return",
                get=no_return,
            ),
            Path(
                "/returns_none",
                get=returns_none,
            ),
            Path(
                "/returns_response",
                get=returns_response,
            ),
            Path(
                "/returns_response_union",
                get=returns_response_union,
            ),
            Path(
                "/returns_model_union",
                get=returns_model_union,
            ),
            Path(
                "/returns_pydantic_model",
                get=returns_pydantic_model,
            ),
        ]
    )

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/no_return": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            },
            "/returns_builtin": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "title": "Response",
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                }
                            },
                        }
                    }
                }
            },
            "/returns_builtin-overriden": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "title": "Response",
                                        "maxItems": 2,
                                        "minItems": 2,
                                        "type": "array",
                                        "items": [
                                            {"type": "string"},
                                            {"type": "string"},
                                        ],
                                    }
                                }
                            },
                        }
                    }
                }
            },
            "/returns_model_union": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "title": "Response",
                                        "anyOf": [
                                            {"type": "string"},
                                            {"type": "integer"},
                                        ],
                                    }
                                }
                            },
                        }
                    }
                }
            },
            "/returns_none": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            },
            "/returns_pydantic_model": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Model"}
                                }
                            },
                        }
                    }
                }
            },
            "/returns_response": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            },
            "/returns_response_union": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {}},
                        }
                    }
                }
            },
        },
        "components": {
            "schemas": {
                "Model": {
                    "title": "Model",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "integer"}},
                }
            }
        },
    }

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi


def test_response_description_from_status_code() -> None:
    async def endpoint() -> None:
        ...

    app = App(
        routes=[
            Path(
                "/",
                get=Operation(
                    endpoint,
                    response_status_code=201,
                    responses={429: ResponseSpec(), "5XX": ResponseSpec()},
                ),
            )
        ]
    )

    expected_openapi: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "429": {"description": "Too Many Requests"},
                        "5XX": {"description": "Server Error"},
                        "201": {
                            "description": "Created",
                            "content": {"application/json": {}},
                        },
                    }
                }
            }
        },
    }

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi
