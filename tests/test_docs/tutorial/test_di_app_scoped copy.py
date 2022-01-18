# from typing import Any, Dict

# from docs_src.tutorial.dependency_injection import app
# from xpresso.testclient import TestClient


# def test_add_user():
#     with TestClient(app) as client:
#         response = client.post("/users/register", json="username")
#         assert response.status_code == 200, response.content


# openapi_schema: Dict[str, Any] = {
#     "openapi": "3.0.3",
#     "info": {"title": "API", "version": "0.1.0"},
#     "paths": {
#         "/users/register": {
#             "post": {
#                 "responses": {
#                     "200": {"description": "Successful Response"},
#                     "422": {
#                         "description": "Validation Error",
#                         "content": {
#                             "application/json": {
#                                 "schema": {
#                                     "$ref": "#/components/schemas/HTTPValidationError"
#                                 }
#                             }
#                         },
#                     },
#                 },
#                 "requestBody": {
#                     "content": {
#                         "application/json": {
#                             "schema": {"title": "User", "type": "string"}
#                         }
#                     },
#                     "required": True,
#                 },
#             }
#         },
#         "/users/{name}/greet": {
#             "get": {
#                 "responses": {
#                     "200": {
#                         "description": "Successful Response",
#                         "content": {
#                             "application/json": {
#                                 "schema": {"title": "Response", "type": "string"}
#                             }
#                         },
#                     },
#                     "422": {
#                         "description": "Validation Error",
#                         "content": {
#                             "application/json": {
#                                 "schema": {
#                                     "$ref": "#/components/schemas/HTTPValidationError"
#                                 }
#                             }
#                         },
#                     },
#                 },
#                 "parameters": [
#                     {
#                         "required": True,
#                         "style": "simple",
#                         "explode": False,
#                         "schema": {"title": "Name", "type": "string"},
#                         "name": "name",
#                         "in": "path",
#                     }
#                 ],
#             }
#         },
#     },
#     "components": {
#         "schemas": {
#             "ValidationError": {
#                 "title": "ValidationError",
#                 "required": ["loc", "msg", "type"],
#                 "type": "object",
#                 "properties": {
#                     "loc": {
#                         "title": "Location",
#                         "type": "array",
#                         "items": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
#                     },
#                     "msg": {"title": "Message", "type": "string"},
#                     "type": {"title": "Error Type", "type": "string"},
#                 },
#             },
#             "HTTPValidationError": {
#                 "title": "HTTPValidationError",
#                 "type": "object",
#                 "properties": {
#                     "detail": {
#                         "title": "Detail",
#                         "type": "array",
#                         "items": {"$ref": "#/components/schemas/ValidationError"},
#                     }
#                 },
#             },
#         }
#     },
# }


# def test_openapi_schema():
#     with TestClient(app) as client:
#         response = client.get("/openapi.json")
#         assert response.status_code == 200, response.content
#         assert response.json() == openapi_schema
