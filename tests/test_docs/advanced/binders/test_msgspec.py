import sys

import pytest


@pytest.mark.skipif(sys.version_info < (3, 8), reason="msgspec does not support 3.7")
def test_count_items() -> None:
    from docs_src.advanced.binders.msgspec.tests import test_count_items
    test_count_items()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="msgspec does not support 3.7")
def test_openapi_schema() -> None:
    from docs_src.advanced.binders.msgspec.tests import test_openapi_schema
    test_openapi_schema()
