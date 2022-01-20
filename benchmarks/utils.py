import time  # noqa: F401
from random import Random
from typing import Any, Callable, Dict, Mapping, Tuple

import anyio  # noqa: F401

random = Random(0)


def generate_dag(
    make_depends: Callable[[str, str], str],
    glbls: Mapping[str, Any],
    levels: int,
    nodes_per_level: int,
    dependencies_per_node: int,
    *,
    sync: bool = False,
    sleep: Tuple[float, float] = (0, 0),
) -> Callable[..., int]:
    """Build a complex DAG of async dependencies"""
    sleep_func = time.sleep if sync else anyio.sleep

    template = (
        "def func_{}({}): sleep({});return 1"
        if sync
        else "async def func_{}({}): await sleep({});return 1"
    )
    globals = {**glbls, "sleep": sleep_func}

    funcs: Dict[str, Callable[..., Any]] = {}
    for level in range(levels):
        level_funcs: Dict[str, Callable[..., Any]] = funcs.copy()
        for node in range(nodes_per_level):
            name = f"{level}_{node}"
            # use funcs and not level_funcs here to make sure we get some concurrency
            deps = random.sample(
                list(funcs.keys()),
                k=min(len(funcs), dependencies_per_node),
            )
            params = ", ".join(
                [
                    f"dep_{dep_name}: {make_depends('None', dep_name)}"
                    for dep_name in deps
                ]
            )
            sleep_time = random.uniform(sleep[0], sleep[1])
            func_def = template.format(name, params, sleep_time)
            exec(func_def, globals, level_funcs)
        funcs.update(level_funcs)
    name = "final"
    deps = list(funcs.keys())
    params = ", ".join(
        [f"dep_{dep_name}: {make_depends('None', dep_name)}" for dep_name in deps]
    )
    func_def = template.format(name, params, 0)
    exec(func_def, globals, funcs)
    return funcs["func_final"]
