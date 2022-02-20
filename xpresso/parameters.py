import typing

import xpresso.binders.dependants as param_dependants
from xpresso._utils.compat import Annotated
from xpresso.binders._parameters.extractors.cookie import CookieParameterExtractorMarker
from xpresso.binders._parameters.extractors.header import HeaderParameterExtractorMarker
from xpresso.binders._parameters.extractors.path import PathParameterExtractorMarker
from xpresso.binders._parameters.extractors.query import QueryParameterExtractorMarker
from xpresso.binders._parameters.openapi import OpenAPIParameterMarker
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
) -> param_dependants.ParameterBinderMarker:
    extractor = QueryParameterExtractorMarker(
        alias=alias,
        explode=explode,
        style=style,
    )
    openapi = OpenAPIParameterMarker(
        alias=alias,
        description=description,
        style=style,
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Query,
    )
    return param_dependants.ParameterBinderMarker(
        in_="query",
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
) -> param_dependants.ParameterBinderMarker:
    extractor = PathParameterExtractorMarker(
        alias=alias,
        explode=explode,
        style=style,
    )
    openapi = OpenAPIParameterMarker(
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
    return param_dependants.ParameterBinderMarker(
        in_="path",
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
) -> param_dependants.ParameterBinderMarker:
    extractor = HeaderParameterExtractorMarker(
        alias=alias,
        explode=explode,
        convert_underscores=convert_underscores,
    )
    openapi = OpenAPIParameterMarker(
        alias=alias,
        description=description,
        explode=explode,
        style="simple",
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Header,
    )
    return param_dependants.ParameterBinderMarker(
        in_="header",
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
) -> param_dependants.ParameterBinderMarker:
    extractor = CookieParameterExtractorMarker(
        alias=alias,
        explode=explode,
    )
    openapi = OpenAPIParameterMarker(
        alias=alias,
        description=description,
        style="form",
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        param_cls=openapi_models.Cookie,
    )
    return param_dependants.ParameterBinderMarker(
        in_="cookie",
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


# Convenience type aliases
_T = typing.TypeVar("_T")
FromQuery = Annotated[_T, QueryParam()]
FromHeader = Annotated[_T, HeaderParam()]
FromCookie = Annotated[_T, CookieParam()]
FromPath = Annotated[_T, PathParam()]
