from typing import Any, Dict, List, NamedTuple, Optional, Union

from starlette.requests import HTTPConnection

import xpresso.openapi.models as openapi_models
from xpresso._utils.typing import Protocol


class SupportsExtractor(Protocol):
    def extract(self, connection: HTTPConnection) -> Any:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError

    def __eq__(self, __o: object) -> bool:
        raise NotImplementedError


Model = type
ModelNameMap = Dict[Model, str]


class OpenAPIMetadata(NamedTuple):
    parameters: Optional[List[openapi_models.ConcreteParameter]] = None
    body: Optional[openapi_models.RequestBody] = None
    schemas: Optional[
        Dict[str, Union[openapi_models.Schema, openapi_models.Reference]]
    ] = None


class SupportsOpenAPI(Protocol):
    def get_models(self) -> List[type]:
        """Collect all of the types that OpenAPI schemas will be
        produced from.

        Xpresso will then assign a schema name to each type and pass
        that back via the ModelNameMap parameter.

        This ensures that all schema models have a unique name,
        even if their Python class names conflict.
        """
        ...

    def get_openapi(
        self,
        model_name_map: ModelNameMap,
    ) -> OpenAPIMetadata:
        ...
