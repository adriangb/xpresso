import difflib
import json
import pathlib
import sys
from typing import Any, Callable, Dict

import pytest


@pytest.fixture
def compare_or_create_expected_openapi(
    request: pytest.FixtureRequest,
) -> Callable[[Dict[str, Any], str], None]:

    module: str = request.function.__module__.split(".")[-1]
    filename: str = module + "__" + request.function.__name__

    def check(openapi: Dict[str, Any], suffix: str = "") -> None:
        if suffix:
            suffix = f"__{suffix}__expected_openapi"
        else:
            suffix = "__expected_openapi"
        expected_openapi_path = pathlib.Path(
            sys.modules[request.function.__module__].__file__  # type: ignore[arg-type]
        ).parent / pathlib.Path(f"{filename}{suffix}").with_suffix(".json")
        if expected_openapi_path.exists():
            with open(expected_openapi_path) as f:
                expected_openapi = json.load(f)
            if expected_openapi != openapi:
                diff = "\n".join(
                    difflib.context_diff(
                        json.dumps(
                            expected_openapi, indent=2, sort_keys=True
                        ).splitlines(),
                        json.dumps(openapi, indent=2, sort_keys=True).splitlines(),
                        fromfile=str(expected_openapi_path),
                        tofile="actual openapi.json",
                    )
                )
                raise AssertionError(f"openapi changed:\n{diff}")
        else:
            with open(expected_openapi_path, "w") as f:
                json.dump(openapi, f, indent=2, sort_keys=True)
            raise AssertionError(
                f"{expected_openapi_path} did not exist so it was generated"
            )

    return check
