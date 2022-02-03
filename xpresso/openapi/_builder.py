import inspect
import sys
from collections import ChainMap, Counter
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

if sys.version_info < (3, 9):
    from typing_extensions import get_args, get_origin, get_type_hints
else:
    from typing import get_origin, get_args, get_type_hints

from di import BaseContainer
from pydantic import BaseConfig
from pydantic.fields import ModelField
from pydantic.schema import field_schema, get_flat_models_from_field
from pydantic.typing import NoneType
from starlette.responses import Response
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from xpresso._utils.routing import VisitedRoute
from xpresso._utils.typing import get_model_name_map
from xpresso.binders import dependants as binder_dependants
from xpresso.openapi import models
from xpresso.openapi.constants import REF_PREFIX
from xpresso.responses import JsonResponseSpec, Responses, ResponseSpec
from xpresso.routing.operation import Operation
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router

T = TypeVar("T")

ModelNameMap = Dict[type, str]

Routes = Mapping[str, Tuple[Path, Mapping[str, Operation]]]

SecurityModels = Mapping[binder_dependants.SecurityBinder, models.SecurityScheme]

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
        if dependant.openapi and dependant.openapi.include_in_schema:
            parameters.append(
                dependant.openapi.get_openapi(
                    model_name_map=model_name_map, schemas=schemas
                )
            )
    if parameters:
        return list(sorted(parameters, key=lambda param: param.name))
    return None


def get_request_body(
    dependant: binder_dependants.BodyBinder,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> models.RequestBody:
    if dependant.openapi and dependant.openapi.include_in_schema:
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
    response_specs: Responses,
    model_name_map: ModelNameMap,
    schemas: Dict[str, Any],
) -> Dict[str, models.Response]:
    responses: Dict[str, models.Response] = {}
    for status_code, response in response_specs.items():
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


def get_operation(
    route: Operation,
    model_name_map: ModelNameMap,
    components: Dict[str, Any],
    security_models: Mapping[binder_dependants.SecurityBinder, str],
    tags: List[str],
    response_specs: Responses,
) -> models.Operation:
    data: Dict[str, Any] = {
        "tags": tags or None,
        "summary": route.summary,
        "description": route.description,
        "deprecated": route.deprecated,
        "servers": route.servers or None,
        "external_docs": route.external_docs,
    }
    docstring = getattr(route.endpoint, "__doc__", None)
    if docstring and not data["description"]:
        data["description"] = docstring
    schemas: Dict[str, Any] = {}
    route_dependant = route.dependant
    assert route_dependant is not None
    parameters = get_parameters(
        [
            dep
            for dep in route_dependant.get_flat_subdependants()
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
            for dep in route_dependant.get_flat_subdependants()
            if isinstance(dep, binder_dependants.BodyBinder)
        ),
        None,
    )
    if body_dependant is not None:
        data["requestBody"] = get_request_body(body_dependant, model_name_map, schemas)
    security_dependants: List[binder_dependants.SecurityBinder] = [
        dep
        for dep in route_dependant.get_flat_subdependants()
        if isinstance(dep, binder_dependants.SecurityBinder)
    ]
    if security_dependants:
        security_schemes = components.get("securitySchemes", None) or {}
        components["securitySchemes"] = security_schemes
        data["security"] = [
            {security_models[dep]: list(dep.scopes)}
            for dep in sorted(security_dependants, key=lambda dep: security_models[dep])
        ]
    data["responses"] = get_responses(
        route,
        response_specs=response_specs,
        model_name_map=model_name_map,
        schemas=schemas,
    )
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
    visitor: Iterable[VisitedRoute[Any]],
    model_name_map: ModelNameMap,
    components: Dict[str, Any],
    security_models: Mapping[binder_dependants.SecurityBinder, str],
) -> Dict[str, models.PathItem]:
    paths: Dict[str, models.PathItem] = {}
    for visited_route in visitor:
        if isinstance(visited_route.route, Path):
            path_item = visited_route.route
            if not path_item.include_in_schema:
                continue
            tags: List[str] = []
            responses = dict(cast(Responses, {}))
            include_in_schema = True
            for node in visited_route.nodes:
                if isinstance(node, Router):
                    if not node.include_in_schema:
                        include_in_schema = False
                        break
                    responses.update(node.responses)
                    tags.extend(node.tags)
            if not include_in_schema:
                continue
            tags.extend(path_item.tags)
            responses.update(path_item.responses)
            operations: Dict[str, models.Operation] = {}
            for method, operation in path_item.operations.items():
                if not operation.include_in_schema:
                    continue
                operations[method.lower()] = get_operation(
                    operation,
                    model_name_map=model_name_map,
                    components=components,
                    security_models=security_models,
                    tags=tags + operation.tags,
                    response_specs={**responses, **operation.responses},
                )
            paths[visited_route.path] = models.PathItem(
                description=visited_route.route.description,
                summary=visited_route.route.summary,
                servers=visited_route.route.servers or None,
                **operations,  # type: ignore[arg-type]
            )  # type: ignore  # for Pylance
    return {k: paths[k] for k in sorted(paths.keys())}


def filter_routes(visitor: Iterable[VisitedRoute[Any]]) -> Routes:
    res: Dict[str, Tuple[Path, Dict[str, Operation]]] = {}
    for visited_route in visitor:
        if isinstance(visited_route.route, Path):
            path_item = visited_route.route
            if not path_item.include_in_schema:
                continue
            operations: Dict[str, Operation] = {}
            for method, operation in path_item.operations.items():
                if not operation.include_in_schema:
                    continue
                operations[method.lower()] = operation
            res[visited_route.path] = (path_item, operations)
    return res


def get_flat_models(routes: Routes) -> Set[type]:
    res: Set[type] = set()
    for _, operations in routes.values():
        for operation in operations.values():
            dependant = operation.dependant
            flat_dependencies = dependant.get_flat_subdependants()
            for dep in flat_dependencies:
                if isinstance(
                    dep,
                    (binder_dependants.ParameterBinder, binder_dependants.BodyBinder),
                ):
                    openapi = dep.openapi
                    res.update(openapi.get_models())
    return res


def get_security_models(
    routes: Routes, container: BaseContainer
) -> Mapping[binder_dependants.SecurityBinder, models.SecurityScheme]:
    res: Dict[binder_dependants.SecurityBinder, models.SecurityScheme] = {}
    for _, operations in routes.values():
        for operation in operations.values():
            dependant = operation.dependant
            flat_dependencies = dependant.get_flat_subdependants()
            for dep in flat_dependencies:
                if isinstance(
                    dep,
                    binder_dependants.SecurityBinder,
                ):
                    res[dep] = dep.construct_model(container)
    return res


def get_security_scheme_name_map(
    models: Mapping[binder_dependants.SecurityBinder, models.SecurityScheme]
) -> Mapping[models.SecurityScheme, str]:
    scheme_names = {scheme: binder.scheme_name for binder, scheme in models.items()}
    name_counter = Counter(scheme_names.values())
    schemes_with_duplicate_names = [
        scheme for scheme in scheme_names if name_counter[scheme_names[scheme]] > 1
    ]
    # sort in reverse order so that APIKey(name="key1") gets assigned the deduped name "APIKey_1"
    for scheme in sorted(
        schemes_with_duplicate_names,
        key=lambda scheme: tuple(scheme.dict().items()),
        reverse=True,
    ):
        name = scheme_names[scheme]
        scheme_names[scheme] += f"_{name_counter[name]}"
        name_counter[name] -= 1
    return scheme_names


def genrate_openapi(
    visitor: Iterable[VisitedRoute[Any]],
    container: BaseContainer,
    version: str,
    info: models.Info,
    servers: Optional[Iterable[models.Server]],
) -> models.OpenAPI:
    visitor = list(visitor)
    routes = filter_routes(visitor)
    flat_models = get_flat_models(routes)
    model_name_map = get_model_name_map(flat_models)
    security_binders = get_security_models(routes, container)
    security_scheme_name_map = get_security_scheme_name_map(security_binders)
    security_bider_to_name_map = {
        binder: security_scheme_name_map[scheme]
        for binder, scheme in security_binders.items()
    }
    components_security_schemes = {
        name: scheme for scheme, name in security_scheme_name_map.items()
    }
    components: Dict[str, Any] = {}
    if components_security_schemes:
        components["securitySchemes"] = {
            name: components_security_schemes[name]
            for name in sorted(components_security_schemes.keys())
        }
    paths = get_paths_items(
        visitor, model_name_map, components, security_bider_to_name_map
    )
    return models.OpenAPI(
        openapi=version,
        info=info,
        paths=paths,  # type: ignore[arg-type]
        components=models.Components(**components) if components else None,
        servers=list(servers) if servers else None,
    )
