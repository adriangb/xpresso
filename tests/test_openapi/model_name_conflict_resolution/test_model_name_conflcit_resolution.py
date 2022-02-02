from dataclasses import dataclass
from typing import Any, Dict

from tests.test_openapi.model_name_conflict_resolution.user1 import User as User1
from tests.test_openapi.model_name_conflict_resolution.user2 import User as User2
from xpresso import (
    App,
    ExtractField,
    FromHeader,
    FromJson,
    FromMultipart,
    FromQuery,
    Path,
)
from xpresso.testclient import TestClient


def test_duplicate_model_name_in_parameters() -> None:
    async def endpoint(q1: FromQuery[User1], q2: FromHeader[User2]) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi_json: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                    "parameters": [
                        {
                            "required": True,
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user1__User"
                            },
                            "name": "q1",
                            "in": "query",
                        },
                        {
                            "required": True,
                            "style": "simple",
                            "explode": False,
                            "schema": {
                                "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user2__User"
                            },
                            "name": "q2",
                            "in": "header",
                        },
                    ],
                }
            }
        },
        "components": {
            "schemas": {
                "tests__test_openapi__model_name_conflict_resolution__user1__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "integer"}},
                },
                "tests__test_openapi__model_name_conflict_resolution__user2__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "string"}},
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi_json


def test_duplicate_model_name_in_form_data() -> None:
    @dataclass
    class FormData:
        field1: ExtractField[FromJson[User1]]
        field2: ExtractField[FromJson[User2]]

    async def endpoint(form: FromMultipart[FormData]) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi_json: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                                    "required": ["field1", "field2"],
                                    "type": "object",
                                    "properties": {
                                        "field1": {
                                            "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user1__User"
                                        },
                                        "field2": {
                                            "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user2__User"
                                        },
                                    },
                                },
                                "encoding": {
                                    "field1": {"contentType": "application/json"},
                                    "field2": {"contentType": "application/json"},
                                },
                            }
                        },
                        "required": True,
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "tests__test_openapi__model_name_conflict_resolution__user1__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "integer"}},
                },
                "tests__test_openapi__model_name_conflict_resolution__user2__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "string"}},
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi_json


def test_model_shared_between_params_and_body() -> None:
    async def endpoint(q: FromQuery[User1], b: FromJson[User2]) -> None:
        ...

    app = App([Path("/", get=endpoint)])

    expected_openapi_json: Dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {"description": "Successful Response"},
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
                    "parameters": [
                        {
                            "required": True,
                            "style": "form",
                            "explode": True,
                            "schema": {
                                "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user1__User"
                            },
                            "name": "q",
                            "in": "query",
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/tests__test_openapi__model_name_conflict_resolution__user2__User"
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
                "tests__test_openapi__model_name_conflict_resolution__user1__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "integer"}},
                },
                "tests__test_openapi__model_name_conflict_resolution__user2__User": {
                    "title": "User",
                    "required": ["foo"],
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "string"}},
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

    client = TestClient(app)

    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.content
    assert resp.json() == expected_openapi_json
