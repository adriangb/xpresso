from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple, cast

from di import BaseContainer
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from xpresso._utils.routing import VisitedRoute
from xpresso._utils.typing import get_model_name_map
from xpresso.binders import dependants as binder_dependants
from xpresso.openapi import models
from xpresso.openapi._responses import (
    get_response,
    get_response_specs_from_return_type_hints,
    merge_response_models,
)
from xpresso.openapi._security import get_security_models, get_security_scheme_name_map
from xpresso.openapi.constants import REF_PREFIX
from xpresso.responses import Responses, ResponseSpec
from xpresso.routing.operation import Operation
from xpresso.routing.pathitem import Path
from xpresso.routing.router import Router

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
