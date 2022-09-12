from docs_src.advanced.binders.msgspec import tests as msgspec_binder_tests


def test_count_items() -> None:
    msgspec_binder_tests.test_count_items()


def test_openapi_schema() -> None:
    msgspec_binder_tests.test_openapi_schema()
