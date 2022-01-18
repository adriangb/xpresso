"""Form data deserialization as per https://swagger.io/docs/specification/serialization/#query
"""
import functools
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, cast

if sys.version_info < (3, 8):
    from typing_extensions import Protocol
else:
    from typing import Protocol

from pydantic.fields import ModelField
from starlette.datastructures import UploadFile

from xpresso.binders._extractors.exceptions import InvalidSerialization
from xpresso.binders._extractors.utils import grouped, is_mapping_like, is_sequence_like
from xpresso.typing import Some


class UnexpectedFileReceived(TypeError):
    pass


def get_matches(
    params: Iterable[Tuple[str, Union[str, UploadFile]]], name: str
) -> List[Optional[str]]:
    matches: List[Optional[str]] = []
    for k, v in params:
        if k == name:
            if not isinstance(v, str):
                raise UnexpectedFileReceived(
                    "Expected a string form field but received a file"
                )
            matches.append(v or None)  # convert "" (from param=&other=123) to None
    return matches


def collect_form_sequence(
    params: Iterable[Tuple[str, Union[str, UploadFile]]],
    name: str,
    explode: bool,
    delimiter: str,
) -> Optional[Some[List[Optional[str]]]]:
    matches = get_matches(params, name)
    if not matches:
        return Some(cast(List[Optional[str]], []))
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
            return Some(cast(List[Optional[str]], [None]))
        return Some(cast(List[Optional[str]], match.split(delimiter)))


def collect_object(
    params: Iterable[Tuple[str, Union[str, UploadFile]]],
    name: str,
    explode: bool,
) -> Optional[Some[Dict[str, str]]]:
    if explode:
        # free form params, let validation filter them out
        return Some({k: v for k, v in params if isinstance(v, str)})
    else:
        matches = get_matches(params, name)
        if not matches:
            return None
        if len(matches) != 1:
            raise InvalidSerialization("Invalid form serialziation")
        match = matches[0]
        if not match:
            return Some(cast(Dict[str, str], {}))
        return Some(dict(cast(Iterable[Tuple[str, str]], grouped(match.split(",")))))


def collect_deep_object(
    params: Iterable[Tuple[str, Union[str, UploadFile]]], name: str
) -> Optional[Some[Optional[Dict[str, Any]]]]:
    # deepObject does not support repeated fields so we can put our fields in dict
    param_dict: Dict[str, str] = {k: v for k, v in params if isinstance(v, str)}
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


def collect_scalar(
    params: Iterable[Tuple[str, Union[str, UploadFile]]], name: str
) -> Optional[Some[Optional[str]]]:
    matches = get_matches(params, name)
    if not matches:
        return None
    return Some(matches[0])


delimiters = {
    "form": ",",
    "pipeDelimited": "|",
    "spaceDelimited": " ",
}


class Extractor(Protocol):
    def __call__(
        self, *, name: str, params: Iterable[Tuple[str, Union[str, UploadFile]]]
    ) -> Optional[Some[Any]]:
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
