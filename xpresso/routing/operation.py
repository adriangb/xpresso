import inspect
import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import get_args, get_origin
else:
    from typing import get_args, get_origin

from di.api.dependencies import DependantBase
from di.api.executor import SupportsAsyncExecutor
from di.api.solved import SolvedDependant
from di.container import Container
from di.dependant import JoinedDependant
from di.executors import AsyncExecutor, ConcurrentAsyncExecutor
from starlette.datastructures import URLPath
from starlette.requests import HTTPConnection, Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, NoMatchFound, get_name
from starlette.types import ASGIApp, Receive, Scope, Send

import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso._utils.asgi import XpressoHTTPExtension
from xpresso._utils.endpoint_dependant import Endpoint, EndpointDependant
from xpresso.dependencies.models import Depends, Scopes
from xpresso.encoders.api import Encoder
from xpresso.encoders.json import JsonableEncoder
from xpresso.openapi._utils import merge_response_specs
from xpresso.responses import ResponseModel, ResponseSpec, TypeUnset


class _OperationResponseFactory(typing.NamedTuple):
    status_code: int
    headers: typing.Optional[typing.Mapping[str, str]]
    media_type: typing.Optional[str]
    response_class: typing.Type[Response]

    def __call__(self, content: typing.Any) -> Response:
        return self.response_class(
            content,
            status_code=self.status_code,
            headers=self.headers,  # type: ignore[arg-type]
            media_type=self.media_type,  # type: ignore[arg-type]
        )


class _OperationApp(typing.NamedTuple):
    dependant: SolvedDependant[typing.Any]
    container: Container
    executor: SupportsAsyncExecutor
    response_factory: typing.Callable[[typing.Any], Response]
    response_encoder: Encoder

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        xpresso_scope: "XpressoHTTPExtension" = scope["extensions"]["xpresso"]
        request = xpresso_scope.request = Request(
            scope=scope, receive=receive, send=send
        )
        values: "typing.Dict[typing.Any, typing.Any]" = {
            Request: request,
            HTTPConnection: request,
        }
        async with xpresso_scope.di_container_state.enter_scope(
            "connection"
        ) as connection_state:
            async with connection_state.enter_scope("endpoint") as endpoint_state:
                endpoint_return = await self.container.execute_async(
                    self.dependant,
                    values=values,
                    executor=self.executor,
                    state=endpoint_state,
                )
                if isinstance(endpoint_return, Response):
                    response = endpoint_return
                else:
                    response = self.response_factory(
                        self.response_encoder(endpoint_return)
                    )
                xpresso_scope.response = response
            await response(scope, receive, send)
            xpresso_scope.response_sent = True


def _is_response(tp: type) -> bool:
    return inspect.isclass(tp) and issubclass(tp, Response)


class Operation(BaseRoute):
    def __init__(
        self,
        endpoint: Endpoint,
        *,
        # OpenAPI parameters
        include_in_schema: bool = True,
        tags: typing.Optional[typing.Sequence[str]] = None,
        summary: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        deprecated: typing.Optional[bool] = None,
        operation_id: typing.Optional[bool] = None,
        servers: typing.Optional[typing.Sequence[openapi_models.Server]] = None,
        external_docs: typing.Optional[openapi_models.ExternalDocumentation] = None,
        responses: typing.Optional[
            typing.Mapping[typing.Union[int, str], ResponseSpec]
        ] = None,
        # xpresso params
        name: typing.Optional[str] = None,
        dependencies: typing.Optional[
            typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]]
        ] = None,
        execute_dependencies_concurrently: bool = False,
        response_factory: typing.Optional[
            typing.Callable[[typing.Any], Response]
        ] = None,
        response_encoder: Encoder = JsonableEncoder(),
        sync_to_thread: bool = True,
        # responses
        default_response_status_code: int = 200,
        default_response_model: type = TypeUnset,
        default_response_description: str = "Successful Response",
        default_response_examples: typing.Optional[
            typing.Mapping[str, typing.Union[openapi_models.Example, typing.Any]]
        ] = None,
        default_response_media_type: str = "application/json",
        default_response_header_values: typing.Optional[
            typing.Mapping[str, str]
        ] = None,
        default_response_header_specs: typing.Optional[
            typing.Mapping[str, typing.Union[openapi_models.ResponseHeader, str]]
        ] = None,
        default_response_class: typing.Type[Response] = JSONResponse,
    ) -> None:
        self._app: typing.Optional[ASGIApp] = None
        self.endpoint = endpoint
        self.tags = tuple(tags or ())
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.servers = tuple(servers or ())
        self.external_docs = external_docs
        self.responses = dict(responses or {})
        if default_response_model is TypeUnset:
            sig_return = inspect.signature(endpoint).return_annotation
            if sig_return is not inspect.Parameter.empty:
                response_annotation = typing.get_type_hints(endpoint)["return"]
                if (
                    # get_type_hints returns type(None)
                    # if the func is () -> None we don't add a response model
                    # it is rare to want to _document_ "null" as the response model
                    sig_return
                    is None
                ) or (
                    # this is a special case for () -> FileResponse and the like
                    _is_response(response_annotation)
                    or get_origin(response_annotation) is typing.Union
                    and any(_is_response(tp) for tp in get_args(response_annotation))
                ):
                    response_annotation = TypeUnset
                if response_annotation is not TypeUnset:
                    default_response_model = response_annotation
        default_content = {
            default_response_media_type: ResponseModel(
                model=default_response_model,
                examples=default_response_examples,
            )
        }
        if default_response_status_code in self.responses:
            if self.responses[default_response_status_code].content:
                content = self.responses[default_response_status_code].content
            else:
                content = default_content
            self.responses[default_response_status_code] = merge_response_specs(
                ResponseSpec(
                    description=default_response_description,
                    content=content,
                    headers=default_response_header_specs,
                ),
                self.responses[default_response_status_code],
            )
        else:
            self.responses[default_response_status_code] = ResponseSpec(
                description=default_response_description,
                content=default_content,
                headers=default_response_header_specs,
            )
        self.dependencies = tuple(
            dep if not isinstance(dep, Depends) else dep.as_dependant()
            for dep in dependencies or ()
        )
        self.execute_dependencies_concurrently = execute_dependencies_concurrently
        self.response_factory = (
            response_factory
            or _OperationResponseFactory(
                status_code=default_response_status_code,
                headers=default_response_header_values,
                media_type=default_response_media_type,
                response_class=default_response_class,
            ).__call__
        )
        self.response_encoder = response_encoder
        self.include_in_schema = include_in_schema
        self.name: str = get_name(endpoint) if name is None else name  # type: ignore
        self.sync_to_thread = sync_to_thread

    async def handle(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if self._app is None:
            raise RuntimeError("Operation cannot be used outside of a Xpresso App")
        return await self._app(scope, receive, send)

    def solve(
        self,
        container: Container,
        dependencies: typing.Iterable[typing.Union[DependantBase[typing.Any], Depends]],
    ) -> None:
        deps = [
            dep if not isinstance(dep, Depends) else dep.as_dependant()
            for dep in dependencies or ()
        ]
        self.dependant = container.solve(
            JoinedDependant(
                EndpointDependant(self.endpoint, sync_to_thread=self.sync_to_thread),
                siblings=[*deps, *self.dependencies],
            ),
            scopes=Scopes,
        )
        flat = self.dependant.get_flat_subdependants()
        bodies = [dep for dep in flat if isinstance(dep, param_dependants.BodyBinder)]
        if len(bodies) > 1:
            raise ValueError("There can only be 1 top level body per operation")
        executor: SupportsAsyncExecutor
        if self.execute_dependencies_concurrently:
            executor = ConcurrentAsyncExecutor()
        else:
            executor = AsyncExecutor()
        self._app = _OperationApp(  # type: ignore[assignment]
            container=container,
            dependant=self.dependant,
            executor=executor,
            response_encoder=self.response_encoder,
            response_factory=self.response_factory,
        )

    def url_path_for(self, name: str, **path_params: str) -> URLPath:
        if path_params:
            raise NoMatchFound(name, path_params)
        if name != self.name:
            raise NoMatchFound(name, path_params)
        return URLPath("/")

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, type(self)) and self.endpoint is __o.endpoint
