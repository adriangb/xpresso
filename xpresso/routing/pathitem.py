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


class _PathApp(typing.NamedTuple):
    operations: typing.Mapping[str, Operation]

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
        for param, operation in (
            (get, "GET"),
            (head, "HEAD"),
            (post, "POST"),
            (put, "PUT"),
            (patch, "PATCH"),
            (delete, "DELETE"),
            (connect, "CONNECT"),
            (options, "OPTIONS"),
            (trace, "TRACE"),
        ):
            if param:
                operations[operation] = (
                    param if isinstance(param, Operation) else Operation(param)
                )
        self.operations = operations
        super().__init__(  # type: ignore  # for Pylance
            path=path,
            # this needs to be an object so that Starlette
            # detects it as an ASGI app and passes us the raw Scope, Receive and Send
            # as well as not wrapping it in a threadpool
            endpoint=_PathApp(operations),  # type: ignore[arg-type]
            name=name,  # type: ignore[arg-type]
            include_in_schema=include_in_schema,
            methods=list(operations.keys()),
        )
