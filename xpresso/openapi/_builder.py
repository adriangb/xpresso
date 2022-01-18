import inspect
import sys
from collections import ChainMap
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
)

if sys.version_info < (3, 9):
    from typing_extensions import get_args, get_origin, get_type_hints
else:
    from typing import get_origin, get_args, get_type_hints

from pydantic import BaseConfig, BaseModel
from pydantic.fields import ModelField
from pydantic.schema import field_schema, get_flat_models_from_field, get_model_name_map
from pydantic.typing import NoneType
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from xpresso._utils.routing import visit_routes
from xpresso.binders import dependants as binder_dependants
from xpresso.openapi import models
from xpresso.openapi.constants import REF_PREFIX
from xpresso.responses import JsonResponseSpec, ResponseSpec
from xpresso.routing import APIRouter, Operation, Path
from xpresso.security._base import SecurityBase
from xpresso.security._dependants import Security

ModelNameMap = Dict[Union[Type[BaseModel], Type[Enum]], str]


SecurityModels = Mapping[Security, SecurityBase]

validation_error_definition = {
    "title": "ValidationError",
    "type": "object",
    "properties": {
        "loc": {
            "title": "Location",
            "type": "array",
            "items": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        },
        "msg": {"title": "Message", "type": "string"},
        "type": {"title": "Error Type", "type": "string"},
    },
    "required": ["loc", "msg", "type"],
}

validation_error_response_definition = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Detail",
            "type": "array",
            "items": {"$ref": REF_PREFIX + "ValidationError"},
        }
    },
}


def get_response_models_from_return_hint(
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
            else:
                if inspect.isclass(tp) and issubclass(tp, NoneType):
                    return [ResponseSpec(description=description)]
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
        else:
            if inspect.isclass(tp) and issubclass(tp, NoneType):
                return [ResponseSpec(description=description)]
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
    return get_response_models_from_return_hint(hints["return"])


def get_parameters(
    deps: List[binder_dependants.ParameterBinder],
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> Optional[List[models.ConcreteParameter]]:
    parameters: List[models.ConcreteParameter] = []
    for dependant in deps:
        if dependant.openapi:
            parameters.append(
                dependant.openapi.get_openapi(
                    model_name_map=model_name_map, schemas=schemas
                )
            )
    return parameters or None


def get_request_body(
    dependant: binder_dependants.BodyBinder,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> models.RequestBody:
    if dependant.openapi:
        return dependant.openapi.get_openapi(
            model_name_map=model_name_map, schemas=schemas
        )
    return models.RequestBody(content={})


def get_response_schema(
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
    if spec.model is not None and spec.media_type is not None:
        schema = get_response_schema(spec.model, model_name_map, schemas)
        examples: Optional[Dict[str, models.Example]]
        if spec.examples:
            examples = {
                n: ex if isinstance(ex, models.Example) else models.Example(value=ex)
                for n, ex in spec.examples.items()
            }
        else:
            examples = None
        content = {spec.media_type: {"schema": schema, "examples": examples}}
        model = models.Response(
            description=spec.description, headers=spec.headers, content=content
        )
    else:
        model = models.Response(
            description=spec.description,
            headers=spec.headers,
            content=None,
        )

    return model


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
    descriptions: List[str] = []
    for m in mods:
        if m.content and m.description:
            descriptions.append(f"- {next(iter(m.content.keys()))}: {m.description}")
    description = "\n".join(descriptions)
    if default_description:
        description = description or default_description
    headers = dict(ChainMap(*((m.headers or {}) for m in mods))) or None
    content = dict(ChainMap(*((m.content or {}) for m in mods))) or None
    return models.Response(description=description, headers=headers, content=content)


def get_responses(
    route: Operation,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> Dict[str, models.Response]:
    responses: Dict[str, models.Response] = {}
    for status_code, response in route.responses.items():
        status = str(status_code)
        if (
            status in responses
            or f"{status[0]}XX" in responses
            or (
                status.endswith("XX")
                and any(s.startswith(status[0]) for s in responses)
            )
        ):
            raise ValueError("Duplicate response status codes are not allowed")
        if isinstance(response, ResponseSpec):
            model = get_response(response, model_name_map, schemas)
        else:
            # iterable of response specs
            model = merge_response_models(
                (get_response(r, model_name_map, schemas) for r in response),
                default_description="Successful Response",
            )
        responses[status] = model
    if responses:
        return responses
    responses_from_type_hints = get_response_specs_from_return_type_hints(
        route.endpoint
    )
    responses_from_type_hints = responses_from_type_hints or [
        ResponseSpec(description="Successful Response")
    ]
    response_model = merge_response_models(
        (
            get_response(spec, model_name_map, schemas)
            for spec in responses_from_type_hints
        ),
        default_description="Successful Response",
    )
    return {"200": response_model}


class SecurityModel(NamedTuple):
    scopes: Sequence[str]
    model: SecurityBase


def get_security_schemes(
    security_models: Sequence[SecurityModel],
    security_schemes: Dict[str, models.SecurityBase],
) -> List[Dict[str, Sequence[str]]]:
    security: Dict[str, Sequence[str]] = {}
    for m in security_models:
        security[m.model.scheme_name] = m.scopes
        security_schemes[m.model.scheme_name] = m.model.model
    return [security]


def get_operation(
    route: Operation,
    model_name_map: ModelNameMap,
    components: Dict[str, Any],
    security_models: Mapping[Security, SecurityBase],
) -> models.Operation:
    data: Dict[str, Any] = {
        "tags": list(route.tags) if route.tags else None,
        "summary": route.summary,
        "deprecated": route.deprecated,
        "servers": route.servers,
        "external_docs": route.external_docs,
    }
    docstring = getattr(route.endpoint, "__doc__", None)
    if docstring:
        data["description"] = docstring
    schemas: Dict[str, Any] = {}
    route_dependant = route.dependant
    assert route_dependant is not None
    parameters = get_parameters(
        [
            dep
            for dep in route_dependant.dag
            if isinstance(dep, binder_dependants.ParameterBinder)
        ],
        model_name_map,
        schemas,
    )
    if parameters:
        data["parameters"] = parameters
    body_dependant = next(
        (
            dep
            for dep in route_dependant.dag
            if isinstance(dep, binder_dependants.BodyBinder)
        ),
        None,
    )
    if body_dependant is not None:
        data["requestBody"] = get_request_body(body_dependant, model_name_map, schemas)
    security_dependants: List[Security] = [
        dep for dep in route_dependant.dag if isinstance(dep, Security)
    ]
    if security_dependants:
        security_schemes = components.get("securitySchemes", None) or {}
        components["securitySchemes"] = security_schemes
        data["security"] = get_security_schemes(
            [
                SecurityModel(list(d.scopes), security_models[d])
                for d in security_dependants
            ],
            security_schemes,
        )
    data["responses"] = get_responses(route, model_name_map, schemas)
    if not data["responses"]:
        data["responses"] = {"200": {"description": "Successful Response"}}
    if schemas:
        components["schemas"] = {**components.get("schemas", {}), **schemas}
    http422 = str(HTTP_422_UNPROCESSABLE_ENTITY)
    if (data.get("parameters", None) or data.get("requestBody", None)) and not any(
        status in data["responses"] for status in (http422, "4XX", "default")
    ):
        data["responses"][http422] = {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": REF_PREFIX + "HTTPValidationError"}
                }
            },
        }
        if "ValidationError" not in schemas:
            components["schemas"] = components.get("schemas", None) or {}
            components["schemas"].update(
                {
                    "ValidationError": validation_error_definition,
                    "HTTPValidationError": validation_error_response_definition,
                }
            )
    return models.Operation(**data)


def get_paths_items(
    router: APIRouter,
    model_name_map: ModelNameMap,
    components: Dict[str, Any],
    security_models: Mapping[Security, SecurityBase],
) -> Dict[str, models.PathItem]:
    paths: Dict[str, models.PathItem] = {}
    for visited_route in visit_routes([router]):
        if isinstance(visited_route.route, Path):
            operations: Dict[str, models.Operation] = {}
            for method, operation in visited_route.route.operations.items():
                operations[method.lower()] = get_operation(
                    operation,
                    model_name_map=model_name_map,
                    components=components,
                    security_models=security_models,
                )
            paths[visited_route.path] = models.PathItem(
                description=visited_route.route.description,
                summary=visited_route.route.summary,
                **operations,  # type: ignore[arg-type]
            )  # type: ignore  # for Pylance
    return paths


def genrate_openapi(
    version: str,
    info: models.Info,
    router: APIRouter,
    security_models: Mapping[Security, SecurityBase],
) -> models.OpenAPI:
    model_name_map: ModelNameMap = {}
    components: Dict[str, Any] = {}
    paths = get_paths_items(router, model_name_map, components, security_models)
    return models.OpenAPI(
        openapi=version,
        info=info,
        paths=paths,  # type: ignore[arg-type]
        components=models.Components(**components) if components else None,
    )
