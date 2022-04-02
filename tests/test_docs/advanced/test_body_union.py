from typing import Any, Callable, Dict

from docs_src.advanced.body_union import app
from xpresso.testclient import TestClient

client = TestClient(app)


def test_openapi(compare_or_create_expected_openapi: Callable[[Dict[str, Any]], None]):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    compare_or_create_expected_openapi(response.json())


def test_post_form():
    response = client.post("/items/", data={"name": "hammer", "price": 1.0})
    assert response.status_code == 200
    assert response.json() == {"hammer": 1.0}


def test_post_json():
    response = client.post("/items/", json={"name": "hammer", "price": 1.0})
    assert response.status_code == 200
    assert response.json() == {"hammer": 1.0}


def test_post_unsupported_media_type():
    response = client.post("/items/", headers={"Content-Type": "text/plain"})
    assert response.status_code == 415
    assert response.json() == {'detail': [{'loc': ['headers', 'content-type'], 'msg': 'Media type text/plain is not supported', 'type': 'value_error'}]}


def test_post_invalid_json():
    response = client.post("/items/", json={"name": "hammer"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'price'], 'msg': 'field required', 'type': 'value_error.missing'}]}


def test_post_invalid_form():
    response = client.post("/items/", data={"name": "hammer"})
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'price'], 'msg': 'field required', 'type': 'value_error.missing'}]}
