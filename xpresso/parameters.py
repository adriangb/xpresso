import typing

import xpresso.binders.dependants as dependants
from xpresso._utils.typing import Annotated
from xpresso.binders._binders import (
    cookie_params,
    header_params,
    param_openapi,
    path_params,
    query_params,
)
from xpresso.openapi import models as openapi_models

Example = typing.Union[openapi_models.Example, typing.Any]


def QueryParam(
    *,
    alias: typing.Optional[str] = None,
    style: openapi_models.QueryParamStyles = "form",
    explode: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    deprecated: typing.Optional[bool] = None,
    include_in_schema: bool = True,
) -> dependants.BinderMarker:
    extractor = query_params.ExtractorMarker(
        alias=alias,
        explode=explode,
        style=style,
    )
    openapi = param_openapi.OpenAPIMarker(
        alias=alias,
        description=description,
        style=style,
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Query,
    )
    return dependants.BinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def PathParam(
    *,
    alias: typing.Optional[str] = None,
    style: openapi_models.PathParamStyles = "simple",
    explode: bool = False,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    deprecated: typing.Optional[bool] = None,
    include_in_schema: bool = True,
) -> dependants.BinderMarker:
    extractor = path_params.ExtractorMarker(
        alias=alias,
        explode=explode,
        style=style,
    )
    openapi = param_openapi.OpenAPIMarker(
        alias=alias,
        description=description,
        style=style,
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Path,
        required=True,
    )
    return dependants.BinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def HeaderParam(
    *,
    convert_underscores: bool = True,
    alias: typing.Optional[str] = None,
    explode: bool = False,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    deprecated: typing.Optional[bool] = None,
    include_in_schema: bool = True,
) -> dependants.BinderMarker:
    extractor = header_params.ExtractorMarker(
        alias=alias,
        explode=explode,
        convert_underscores=convert_underscores,
    )
    openapi = param_openapi.OpenAPIMarker(
        alias=alias,
        description=description,
        explode=explode,
        style="simple",
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Header,
    )
    return dependants.BinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def CookieParam(
    *,
    alias: typing.Optional[str] = None,
    explode: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    deprecated: typing.Optional[bool] = None,
    include_in_schema: bool = True,
) -> dependants.BinderMarker:
    extractor = cookie_params.ExtractorMarker(
        alias=alias,
        explode=explode,
    )
    openapi = param_openapi.OpenAPIMarker(
        alias=alias,
        description=description,
        style="form",
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Cookie,
    )
    return dependants.BinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


# Convenience type aliases
_T = typing.TypeVar("_T")
FromQuery = Annotated[_T, QueryParam()]
FromHeader = Annotated[_T, HeaderParam()]
FromCookie = Annotated[_T, CookieParam()]
FromPath = Annotated[_T, PathParam()]
