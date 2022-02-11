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
from xpresso.openapi import models as openapi_models

Example = typing.Union[openapi_models.Example, typing.Any]


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


# Convenience type aliases
_T = typing.TypeVar("_T")
FromJson = Annotated[_T, Json()]
FromFile = Annotated[_T, File()]
FromFormField = Annotated[_T, FormEncodedField()]
ExtractField = Annotated[_T, FormField()]
ExtractRepeatedField = Annotated[_T, RepeatedFormField()]
FromFormData = Annotated[_T, Form()]
FromMultipart = Annotated[_T, Multipart()]
ByContentType = Annotated[_T, ContentTypeDiscriminatedBody()]
