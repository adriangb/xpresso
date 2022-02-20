import inspect
from collections import ChainMap
from typing import Any, Callable, Dict, Iterable, List, Optional, TypeVar, Union

from pydantic import BaseConfig
from pydantic.fields import ModelField
from pydantic.schema import field_schema, get_flat_models_from_field
from pydantic.typing import NoneType
from starlette.responses import Response

from xpresso._utils.compat import get_args, get_origin, get_type_hints
from xpresso._utils.typing import get_model_name_map
from xpresso.openapi import models
from xpresso.openapi.constants import REF_PREFIX
from xpresso.responses import JsonResponseSpec, ResponseSpec

T = TypeVar("T")

ModelNameMap = Dict[type, str]


def _get_response_models_from_return_hint(
    return_hint: type,
) -> List[ResponseSpec]:
    res: Dict[str, ResponseSpec] = {}
    description = ""
    if get_origin(return_hint) is Union:
        tps: List[Any] = []
        for tp in get_args(return_hint):
            if inspect.isclass(tp) and issubclass(tp, Response):
                if tp.media_type is not None:
                    res[tp.media_type] = ResponseSpec(
                        description=description,
                        media_type=tp.media_type,
                    )
            elif inspect.isclass(tp) and issubclass(tp, NoneType):
                return [ResponseSpec(description=description)]
            else:
                tps.append(tp)
        if tps:
            res["application/json"] = JsonResponseSpec(
                description=description,
                model=Union[tuple(tps)],
            )
    else:
        tp = return_hint
        if inspect.isclass(tp) and issubclass(tp, Response):
            if tp.media_type is not None:
                res[tp.media_type] = ResponseSpec(
                    description=description,
                    media_type=tp.media_type,
                )
        elif inspect.isclass(tp) and issubclass(tp, NoneType):
            return [ResponseSpec(description=description)]
        else:
            res["application/json"] = JsonResponseSpec(
                description=description,
                model=tp,
            )
    return list(res.values()) or [ResponseSpec(description=description)]


def get_response_specs_from_return_type_hints(
    endpoint: Callable[..., Any]
) -> List[ResponseSpec]:
    hints = get_type_hints(endpoint, include_extras=True)
    if "return" not in hints:
        return []
    return _get_response_models_from_return_hint(hints["return"])


def _get_response_schema(
    type_: type, model_name_map: ModelNameMap, schemas: Dict[str, Any]
) -> Dict[str, Any]:
    field = ModelField.infer(
        name="response",
        value=...,
        annotation=type_,
        class_validators={},
        config=BaseConfig,
    )
    model_name_map.update(
        get_model_name_map(
            get_flat_models_from_field(
                field,
                model_name_map.keys(),  # type: ignore[arg-type]
            )
        )
    )
    schema, refs, _ = field_schema(
        field, by_alias=True, ref_prefix=REF_PREFIX, model_name_map=model_name_map
    )
    schemas.update(refs)
    return schema


def get_response(
    spec: ResponseSpec,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> models.Response:
    if spec.model is None or spec.media_type is None:
        return models.Response(
            description=spec.description,
            headers=spec.headers,
            content=None,
        )

    schema = _get_response_schema(spec.model, model_name_map, schemas)
    examples: Optional[Dict[str, models.Example]]
    if spec.examples:
        examples = {
            n: ex if isinstance(ex, models.Example) else models.Example(value=ex)
            for n, ex in spec.examples.items()
        }
    else:
        examples = None
    content = {spec.media_type: {"schema": schema, "examples": examples}}
    return models.Response(
        description=spec.description, headers=spec.headers, content=content
    )


def merge_response_models(
    mods: Iterable[models.Response], default_description: Optional[str] = None
) -> models.Response:
    mods = list(mods)
    if len(mods) == 1:
        mod = next(iter(mods))
        return models.Response(
            description=mod.description or default_description or "",
            headers=mod.headers,
            content=mod.content,
        )
    descriptions: List[str] = [
        f"- {next(iter(m.content.keys()))}: {m.description}"
        for m in mods
        if m.content and m.description
    ]

    description = "\n".join(descriptions)
    if default_description:
        description = description or default_description
    headers = dict(ChainMap(*((m.headers or {}) for m in mods))) or None
    content = dict(ChainMap(*((m.content or {}) for m in mods))) or None
    return models.Response(description=description, headers=headers, content=content)
