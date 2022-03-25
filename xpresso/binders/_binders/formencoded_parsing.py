"""Form data deserialization as per https://swagger.io/docs/specification/serialization/#query
"""
import functools
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic.fields import ModelField

from xpresso._utils.pydantic_utils import is_mapping_like, is_sequence_like
from xpresso._utils.typing import Protocol
from xpresso.binders._binders.grouped import grouped
from xpresso.typing import Some


class InvalidSerialization(ValueError):
    pass


def get_matches(params: Iterable[Tuple[str, str]], name: str) -> List[Optional[str]]:
    matches: List[Optional[str]] = []
    for k, v in params:
        if k == name:
            matches.append(v or None)  # convert "" (from param=&other=123) to None
    return matches


def collect_form_sequence(
    params: Iterable[Tuple[str, str]],
    name: str,
    explode: bool,
    delimiter: str,
) -> Optional[Some]:
    matches = get_matches(params, name)
    if not matches:
        return Some([])
    if explode:
        # No further processing needed since the delimiter is &
        # for all styles
        return Some(matches)
    else:
        # We need to split these up manually
        if len(matches) != 1:
            raise InvalidSerialization("Invalid form serialziation")
        match = matches[0]
        if not match:
            # user gave us ?param=&other=abc
            return Some([None])
        return Some(list(match.split(delimiter)))


def collect_object(
    params: Iterable[Tuple[str, str]],
    name: str,
    explode: bool,
) -> Optional[Some]:
    if explode:
        # free form params, let validation filter them out
        return Some(dict(params))
    else:
        matches = get_matches(params, name)
        if not matches:
            return None
        if len(matches) != 1:
            raise InvalidSerialization("Invalid form serialziation")
        match = matches[0]
        if not match:
            return Some({})
        return Some(dict(grouped(match.split(","))))  # type: ignore[arg-type]


def collect_deep_object(params: Iterable[Tuple[str, str]], name: str) -> Optional[Some]:
    # deepObject does not support repeated fields so we can put our fields in dict
    param_dict: Dict[str, str] = dict(params)
    if not param_dict:
        return None
    res: Dict[str, Any] = {}
    path_regex = re.compile(rf"{name}\[(\w+)\]")
    for path, value in param_dict.items():
        match = path_regex.match(path)
        if not match:
            continue
        field_name = match.group(1)
        res[field_name] = value
    return Some(res or None)


def collect_scalar(params: Iterable[Tuple[str, str]], name: str) -> Optional[Some]:
    params_mapping = dict(params)
    if name not in params_mapping:
        return None
    v = params_mapping[name]
    return Some(v or None)


delimiters = {
    "form": ",",
    "pipeDelimited": "|",
    "spaceDelimited": " ",
}


class Extractor(Protocol):
    def __call__(
        self, *, name: str, params: Iterable[Tuple[str, str]]
    ) -> Optional[Some]:
        ...


def get_extractor(*, style: str, explode: bool, field: ModelField) -> Extractor:
    if style == "deepObject":
        return collect_deep_object
    if style in ("spaceDelimited", "pipeDelimited"):
        return functools.partial(
            collect_form_sequence,
            explode=explode,
            delimiter=delimiters[style],
        )
    # form style
    if is_sequence_like(field):
        return functools.partial(
            collect_form_sequence,
            explode=explode,
            delimiter=delimiters[style],
        )
    if is_mapping_like(field):
        return functools.partial(
            collect_object,
            explode=explode,
        )
    return collect_scalar
