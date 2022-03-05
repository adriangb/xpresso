import typing

import starlette.routing
import starlette.types
from di.api.dependencies import DependantBase
from di.api.providers import DependencyProvider as Endpoint

import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso.dependencies.models import Depends
from xpresso.responses import Responses
from xpresso.routing.operation import Operation


class _PathApp:
    """Thin class wrapper so that Starlette treats us as an ASGI App"""

    __slots__ = ("operations",)

    def __init__(self, operations: typing.Mapping[str, Operation]) -> None:
        self.operations = operations

    def __call__(
        self,
        scope: starlette.types.Scope,
        receive: starlette.types.Receive,
        send: starlette.types.Send,
    ) -> typing.Awaitable[None]:
        return self.operations[scope["method"]].handle(scope, receive, send)


class Path(starlette.routing.Route):
    include_in_schema: bool

    def __init__(
        self,
        path: str,
        *,
        get: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        head: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        post: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        put: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        patch: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        delete: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        connect: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        options: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        trace: typing.Optional[typing.Union[Operation, Endpoint]] = None,
        redirect_slashes: bool = True,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]]
        ] = None,
        # OpenAPI metadata
        include_in_schema: bool = True,
        name: typing.Optional[str] = None,
        summary: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        servers: typing.Optional[typing.Sequence[openapi_models.Server]] = None,
        parameters: typing.Optional[
            typing.Sequence[param_dependants.ParameterBinderMarker]
        ] = None,
        responses: typing.Optional[Responses] = None,
        tags: typing.Optional[typing.Iterable[str]] = None,
    ) -> None:
        if not path.startswith("/"):
            raise ValueError("Routed paths must start with '/'")
        self.path = path
        self.redirect_slashes = redirect_slashes
        self.dependencies = tuple(
            dep if not isinstance(dep, Depends) else dep.as_dependant()
            for dep in dependencies or ()
        )
        self.summary = summary
        self.description = description
        self.servers = tuple(servers or ())
        self.parameters = list(parameters or ())
        self.tags = tuple(tags or ())
        self.responses = dict(responses or {})

        operations: typing.Dict[str, Operation] = {}
        if get:
            operations["GET"] = get if isinstance(get, Operation) else Operation(get)
        if head:
            operations["HEAD"] = (
                head if isinstance(head, Operation) else Operation(head)
            )
        if post:
            operations["POST"] = (
                post if isinstance(post, Operation) else Operation(post)
            )
        if put:
            operations["PUT"] = put if isinstance(put, Operation) else Operation(put)
        if patch:
            operations["PATCH"] = (
                patch if isinstance(patch, Operation) else Operation(patch)
            )
        if delete:
            operations["DELETE"] = (
                delete if isinstance(delete, Operation) else Operation(delete)
            )
        if connect:
            operations["CONNECT"] = (
                connect if isinstance(connect, Operation) else Operation(connect)
            )
        if options:
            operations["OPTIONS"] = (
                options if isinstance(options, Operation) else Operation(options)
            )
        if trace:
            operations["TRACE"] = (
                trace if isinstance(trace, Operation) else Operation(trace)
            )
        self.operations = operations
        super().__init__(  # type: ignore  # for Pylance
            path=path,
            endpoint=_PathApp(operations),
            name=name,  # type: ignore[arg-type]
            include_in_schema=include_in_schema,
            methods=list(operations.keys()),
        )
