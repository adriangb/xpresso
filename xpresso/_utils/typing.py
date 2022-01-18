import inspect

from pydantic import BaseConfig
from pydantic.fields import ModelField


def model_field_from_param(param: inspect.Parameter) -> ModelField:
    return ModelField.infer(
        name=param.name,
        value=param.default if param.default is not param.empty else ...,
        annotation=param.annotation,
        class_validators={},
        config=BaseConfig,
    )
