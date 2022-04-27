from typing import Any, AsyncIterator, Awaitable, Dict, List, Union

from starlette.requests import HTTPConnection

import xpresso.openapi.models as openapi_models
from xpresso._utils.typing import Protocol


class SupportsExtractor(Protocol):
    def extract(
        self, connection: HTTPConnection
    ) -> Union[Awaitable[Any], AsyncIterator[Any]]:
        """Extract data from an incoming connection.

        The `connection` parameter will always be either a Request object or a WebSocket object,
        which are both subclasses of HTTPConnection.
        If you just need access to headers, query params, or any other metadata present in HTTPConnection
        then you can use the parameter directly.
        Otherwise, you can do `isinstance(connection, Request)` before accessing `Request.stream()` and such.

        The return value can be an awaitable or an async iterable (context manager like).
        The iterator versions will be wrapped with `@contextlib.{async}contextmanager`.
        """
        ...

    # __hash__ and __eq__ are required so that the dependency injection system can cache extracted values
    # (for example allowing the user to get multiple references to a request body without parsing twice)

    def __hash__(self) -> int:
        ...

    def __eq__(self, __o: object) -> bool:
        ...


Model = type
ModelNameMap = Dict[Model, str]


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

    def modify_operation_schema(
        self,
        model_name_map: ModelNameMap,
        operation: openapi_models.Operation,
        components: openapi_models.Components,
    ) -> None:
        """Callback to modify the OpenAPI schema.

        Implementers should modify the operation and components as they see fit,
        but take care to not needlessly add keys or try to access keys which may not exist.

        When determining what string name to use to represent a model/schema (for example to add it to components/schemas)
        you MUST use the model_name_map parameter to find the name assigned for each type.
        For example:
        >>> components.schemas[model_name_map[MyModel]] = MyModel.get_schema()
        """
        ...
