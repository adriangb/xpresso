import json
import typing

import xpresso.binders.dependents as dependents
import xpresso.openapi.models as openapi_models
from xpresso._utils.typing import Annotated, Literal
from xpresso.binders._binders import file_body, form_body, json_body, union

Example = typing.Union[openapi_models.Example, typing.Any]


def Json(
    *,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    decoder: json_body.SupportsJsonDecoder = json.loads,
    enforce_media_type: bool = True,
    consume: bool = True,
    include_in_schema: bool = True,
) -> dependents.BinderMarker:
    body_extractor_marker = json_body.ExtractorMarker(
        decoder=decoder,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    body_openapi_marker = json_body.OpenAPIMarker(
        description=description,
        examples=examples,
        include_in_schema=include_in_schema,
    )
    return dependents.BinderMarker(
        extractor_marker=body_extractor_marker,
        openapi_marker=body_openapi_marker,
    )


def RawBody(
    *,
    media_type: typing.Optional[str] = None,
    enforce_media_type: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    format: Literal["binary", "base64"] = "binary",
    consume: bool = True,
    include_in_schema: bool = True,
) -> dependents.BinderMarker:
    extractor_marker = file_body.ExtractorMarker(
        media_type=media_type,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    openapi_marker = file_body.OpenAPIMarker(
        description=description,
        examples=examples,
        media_type=media_type,
        format=format,
        include_in_schema=include_in_schema,
    )
    return dependents.BinderMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def FormField(
    *,
    alias: typing.Optional[str] = None,
    style: openapi_models.FormDataStyles = "form",
    explode: bool = True,
) -> form_body.FormFieldMarker:
    extractor_marker = form_body.FormFieldExtractorMarker(
        alias=alias,
        style=style,
        explode=explode,
    )
    openapi_marker = form_body.FormFieldOpenAPIMarker(
        alias=alias,
        style=style,
        explode=explode,
    )
    return form_body.FormFieldMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def FormFile(
    *,
    alias: typing.Optional[str] = None,
    media_type: typing.Optional[str] = None,
    format: Literal["binary", "base64"] = "binary",
) -> form_body.FormFieldMarker:
    extractor_marker = form_body.FormFileExtractorMarker(
        alias=alias,
    )
    openapi_marker = form_body.FormFileOpenAPIMarker(
        alias=alias,
        format=format,
        media_type=media_type,
    )
    return form_body.FormFieldMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def Form(
    *,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> dependents.BinderMarker:
    extractor_marker = form_body.ExtractorMarker(
        media_type="application/x-www-form-urlencoded",
    )
    openapi_marker = form_body.OpenAPIMarker(
        description=description,
        examples=examples,
        media_type="application/x-www-form-urlencoded",
        include_in_schema=include_in_schema,
    )
    return dependents.BinderMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def Multipart(
    *,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> dependents.BinderMarker:
    extractor_marker = form_body.ExtractorMarker(media_type="multipart/form-data")
    openapi_marker = form_body.OpenAPIMarker(
        description=description,
        examples=examples,
        media_type="multipart/form-data",
        include_in_schema=include_in_schema,
    )
    return dependents.BinderMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def BodyUnion(
    *,
    description: typing.Optional[str] = None,
) -> dependents.BinderMarker:
    extractor_marker = union.ExtractorMarker()
    openapi_marker = union.BodyOpenAPIMarker(
        description=description,
    )
    return dependents.BinderMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


if typing.TYPE_CHECKING:
    from pydantic import BaseModel

    from xpresso import UploadFile


# Convenience type aliases
_T = typing.TypeVar("_T")
_BaseModelT = typing.TypeVar("_BaseModelT", bound=typing.Union["BaseModel", None])
FromJson = Annotated[_BaseModelT, Json()]
_BinaryT = typing.TypeVar(
    "_BinaryT",
    bound=typing.Union[
        bytes,
        "UploadFile",
        typing.AsyncIterator[bytes],
        None,
    ],
)
FromRawBody = Annotated[_BinaryT, RawBody()]
FromFormField = Annotated[_T, FormField()]
_FormFileT = typing.TypeVar(
    "_FormFileT",
    bound=typing.Union[
        bytes, "UploadFile", typing.List[bytes], "typing.List[UploadFile]", None
    ],
)
FromFormFile = Annotated[_FormFileT, FormFile()]
FromFormData = Annotated[_BaseModelT, Form()]
FromMultipart = Annotated[_BaseModelT, Multipart()]
FromBodyUnion = Annotated[_T, BodyUnion()]
