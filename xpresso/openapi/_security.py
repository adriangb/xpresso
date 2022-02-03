from collections import Counter
from typing import Dict, Mapping, Tuple

from di import BaseContainer

from xpresso.binders import dependants as binder_dependants
from xpresso.openapi import models
from xpresso.routing.operation import Operation
from xpresso.routing.pathitem import Path

SecurityModels = Mapping[binder_dependants.SecurityBinder, models.SecurityScheme]


def get_security_models(
    routes: Mapping[str, Tuple[Path, Mapping[str, Operation]]], container: BaseContainer
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
