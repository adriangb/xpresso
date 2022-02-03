import json
import sys
import typing

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

import xpresso.binders.dependants as param_dependants
from xpresso.binders._body.extractors.discriminated import (
    ContentTypeDiscriminatedExtractorMarker,
)
from xpresso.binders._body.extractors.field import (
    FieldExtractorMarker,
    RepeatedFieldExtractorMarker,
)
from xpresso.binders._body.extractors.file import FileBodyExtractorMarker
from xpresso.binders._body.extractors.form import (
    FormDataBodyExtractorMarker,
    MultipartBodyExtractorMarker,
)
from xpresso.binders._body.extractors.form_field import FormFieldBodyExtractorMarker
from xpresso.binders._body.extractors.json import Decoder, JsonBodyExtractorMarker
from xpresso.binders._body.openapi.discriminated import (
    OpenAPIContentTypeDiscriminatedMarker,
)
from xpresso.binders._body.openapi.field import (
    OpenAPIFieldMarker,
    OpenAPIRepeatedFieldMarker,
)
from xpresso.binders._body.openapi.file import OpenAPIFileMarker
from xpresso.binders._body.openapi.form import OpenAPIFormDataMarker
from xpresso.binders._body.openapi.form_field import OpenAPIFormFieldMarker
from xpresso.binders._body.openapi.json import OpenAPIJsonMarker
from xpresso.binders._parameters.extractors.cookie import CookieParameterExtractorMarker
from xpresso.binders._parameters.extractors.header import HeaderParameterExtractorMarker
from xpresso.binders._parameters.extractors.path import PathParameterExtractorMarker
from xpresso.binders._parameters.extractors.query import QueryParameterExtractorMarker
from xpresso.binders._parameters.openapi.cookie import OpenAPICookieParameterMarker
from xpresso.binders._parameters.openapi.header import OpenAPIHeaderParameterMarker
from xpresso.binders._parameters.openapi.path import OpenAPIPathParameterMarker
from xpresso.binders._parameters.openapi.query import OpenAPIQueryParameterMarker
from xpresso.binders.api import SecurityBase
from xpresso.openapi import models as openapi_models

T = typing.TypeVar("T")

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
    openapi = OpenAPIQueryParameterMarker(
        alias=alias,
        description=description,
        style=style,
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
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
    openapi = OpenAPIPathParameterMarker(
        alias=alias,
        description=description,
        style=style,
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
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
    openapi = OpenAPIHeaderParameterMarker(
        alias=alias,
        description=description,
        explode=explode,
        style="simple",
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
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
    openapi = OpenAPICookieParameterMarker(
        alias=alias,
        description=description,
        style="form",
        explode=explode,
        examples=examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
    )
    return param_dependants.ParameterBinderMarker(
        in_="cookie",
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def Json(
    *,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    decoder: Decoder = json.loads,
    enforce_media_type: bool = True,
    consume: bool = True,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = JsonBodyExtractorMarker(
        decoder=decoder,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    openapi = OpenAPIJsonMarker(
        description=description,
        examples=examples,
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def File(
    *,
    media_type: typing.Optional[str] = None,
    enforce_media_type: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    format: Literal["binary", "base64"] = "binary",
    consume: bool = True,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = FileBodyExtractorMarker(
        media_type=media_type,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    openapi = OpenAPIFileMarker(
        description=description,
        examples=examples,
        media_type=media_type,
        format=format,
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def FormEncodedField(
    *,
    alias: typing.Optional[str] = None,
    style: openapi_models.FormDataStyles = "form",
    explode: bool = True,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = FormFieldBodyExtractorMarker(
        alias=alias,
        style=style,
        explode=explode,
    )
    openapi = OpenAPIFormFieldMarker(
        alias=alias,
        style=style,
        explode=explode,
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def FormField(
    *,
    alias: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = FieldExtractorMarker(alias=alias)
    openapi = OpenAPIFieldMarker(
        alias=alias,
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def RepeatedFormField(
    *,
    alias: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = RepeatedFieldExtractorMarker(alias=alias)
    openapi = OpenAPIRepeatedFieldMarker(
        alias=alias,
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def Form(
    *,
    enforce_media_type: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = FormDataBodyExtractorMarker(
        enforce_media_type=enforce_media_type,
    )
    openapi = OpenAPIFormDataMarker(
        description=description,
        examples=examples,
        media_type="application/x-www-form-urlencoded",
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def Multipart(
    *,
    enforce_media_type: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    extractor = MultipartBodyExtractorMarker(
        enforce_media_type=enforce_media_type,
    )
    openapi = OpenAPIFormDataMarker(
        description=description,
        examples=examples,
        media_type="multipart/form-data",
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def ContentTypeDiscriminatedBody(
    *,
    description: typing.Optional[str] = None,
) -> param_dependants.BodyBinderMarker:
    extractor = ContentTypeDiscriminatedExtractorMarker()
    openapi = OpenAPIContentTypeDiscriminatedMarker(
        description=description,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def Security(
    model: typing.Union[SecurityBase, typing.Type[SecurityBase]],
    *,
    scopes: typing.Optional[typing.Sequence[str]] = None,
    scheme_name: typing.Optional[str] = None,
) -> param_dependants.SecurityBinder:
    return param_dependants.SecurityBinder(
        model=model, scopes=scopes, scheme_name=scheme_name
    )


# Convenience type aliases
FromQuery = Annotated[T, QueryParam()]
FromHeader = Annotated[T, HeaderParam()]
FromCookie = Annotated[T, CookieParam()]
FromPath = Annotated[T, PathParam()]
FromJson = Annotated[T, Json()]
FromFile = Annotated[T, File()]
FromFormField = Annotated[T, FormEncodedField()]
ExtractField = Annotated[T, FormField()]
ExtractRepeatedField = Annotated[T, RepeatedFormField()]
FromFormData = Annotated[T, Form()]
FromMultipart = Annotated[T, Multipart()]
ByContentType = Annotated[T, ContentTypeDiscriminatedBody()]
