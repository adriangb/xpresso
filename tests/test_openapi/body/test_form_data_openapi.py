import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from pydantic import BaseModel
from starlette.testclient import TestClient

from xpresso import (
    Form,
    FormField,
    FromFormData,
    FromFormField,
    FromJson,
    FromMultipart,
    Path,
)
from xpresso.applications import App


class FormModel(BaseModel):
    a: int
    b: str


class NestedModel(BaseModel):
    inner: FormModel


def test_form_field_object() -> None:
    class FormDataModel(BaseModel):
        form_object: FromFormField[FormModel]

    async def endpoint(body: FromFormData[FormDataModel]) -> None:
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
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "required": ["form_object"],
                                    "type": "object",
                                    "properties": {
                                        "form_object": {
                                            "$ref": "#/components/schemas/FormModel"
                                        }
                                    },
                                },
                                "encoding": {
                                    "form_object": {"style": "form", "explode": True}
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
                "FormModel": {
                    "title": "FormModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_form_field_custom_encoding() -> None:
    class FormDataModel(BaseModel):
        form_object: Annotated[FormModel, FormField(style="deepObject")]

    async def endpoint(body: FromMultipart[FormDataModel]) -> None:
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
                                    "required": ["form_object"],
                                    "type": "object",
                                    "properties": {
                                        "form_object": {
                                            "$ref": "#/components/schemas/FormModel"
                                        }
                                    },
                                },
                                "encoding": {
                                    "form_object": {
                                        "style": "deepObject",
                                        "explode": True,
                                    }
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
                "FormModel": {
                    "title": "FormModel",
                    "required": ["a", "b"],
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "type": "integer"},
                        "b": {"title": "B", "type": "string"},
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_optional_form_data() -> None:
    class FormDataModel(BaseModel):
        field: str

    async def endpoint(
        body: FromFormData[typing.Optional[FormDataModel]] = None,
    ) -> None:
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
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "required": ["field"],
                                    "type": "object",
                                    "properties": {
                                        "field": {"title": "Field", "type": "string"}
                                    },
                                    "nullable": True,
                                },
                                "encoding": {
                                    "field": {"style": "form", "explode": True}
                                },
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi


def test_include_in_schema() -> None:
    class FormDataModel(BaseModel):
        field: str

    async def test(
        body: Annotated[FormDataModel, Form(include_in_schema=False)]
    ) -> None:
        ...

    app = App([Path("/", post=test)])

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


def test_include_in_schema_field() -> None:
    class FormDataModel(BaseModel):
        field: Annotated[FromJson[str], FormField(include_in_schema=False)]

    async def endpoint(form: FromFormData[FormDataModel]) -> None:
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
                            "application/x-www-form-urlencoded": {
                                "schema": {"type": "object", "properties": {}}
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

    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    assert resp.json() == expected_openapi
