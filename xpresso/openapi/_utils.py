from typing import Any, Mapping, Union

from xpresso.encoders import JsonableEncoder
from xpresso.openapi import models as openapi_models
from xpresso.responses import ResponseSpec

ENCODER = JsonableEncoder()


def merge_response_specs(r1: ResponseSpec, r2: ResponseSpec) -> ResponseSpec:
    return ResponseSpec(
        description=r2.description or r1.description,
        headers={**(r2.headers or {}), **(r1.headers or {})} or None,
        content={**(r2.content or {}), **(r1.content or {})} or None,
    )


def parse_examples(
    examples: Mapping[str, Union[openapi_models.Example, Any]]
) -> openapi_models.Examples:
    return {
        k: v
        if isinstance(v, openapi_models.Example)
        else openapi_models.Example(value=ENCODER(v))
        for k, v in examples.items()
    }
