from docs_src.advanced.binders.msgpack import tests as msgpack_binder_tests


def test_echo_item() -> None:
    msgpack_binder_tests.test_echo_item()


def test_openapi_schema() -> None:
    msgpack_binder_tests.test_openapi_schema()
