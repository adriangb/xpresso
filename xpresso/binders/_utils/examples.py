from typing import Any, Mapping, Union

from xpresso.openapi import models as openapi_models


def parse_examples(
    examples: Mapping[str, Union[openapi_models.Example, Any]]
) -> openapi_models.Examples:
    return {
        k: v
        if isinstance(v, openapi_models.Example)
        else openapi_models.Example(value=v)
        for k, v in examples.items()
    }
