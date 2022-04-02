import json
import pathlib
import sys
from typing import Any, Callable, Dict

import pytest


@pytest.fixture
def get_or_create_expected_openapi(
    request: pytest.FixtureRequest,
) -> Callable[[Dict[str, Any], str], Dict[str, Any]]:

    module: str = request.function.__module__.split(".")[-1]
    filename: str = module + "__" + request.function.__name__

    def check(openapi: Dict[str, Any], suffix: str = "") -> Dict[str, Any]:
        if suffix:
            suffix = f"__{suffix}__expected_openapi"
        else:
            suffix = "__expected_openapi"
        expected_openapi_path = pathlib.Path(
            sys.modules[request.function.__module__].__file__  # type: ignore[arg-type]
        ).parent / pathlib.Path(f"{filename}{suffix}").with_suffix(".json")
        if expected_openapi_path.exists():
            with open(expected_openapi_path) as f:
                return json.load(f)
        else:
            with open(expected_openapi_path, "w") as f:
                json.dump(openapi, f)
            raise AssertionError(
                f"{expected_openapi_path} did not exist so it was generated"
            )

    return check
