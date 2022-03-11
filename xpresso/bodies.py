import typing
from json import loads as json_loads

import xpresso.binders._body.discriminated as discriminated
import xpresso.binders._body.files as files
import xpresso.binders._body.forms as forms
import xpresso.binders._body.json as json
import xpresso.binders.dependants as param_dependants
import xpresso.openapi.models as openapi_models
from xpresso._utils.compat import Annotated, Literal
from xpresso.binders._body.form_field import FormFieldMarker

Example = typing.Union[openapi_models.Example, typing.Any]


def Json(
    *,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    decoder: json.SupportsJsonDecoder = json_loads,
    enforce_media_type: bool = True,
    consume: bool = True,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    body_extractor_marker = json.BodyExtractorMarker(
        decoder=decoder,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    field_extractor_marker = json.FieldExtractorMarker(decoder=decoder)
    body_openapi_marker = json.BodyOpenAPIMarker(
        description=description,
        examples=examples,
        include_in_schema=include_in_schema,
    )
    openapi_field_marker = json.FieldOpenAPIMarker()
    return param_dependants.BodyBinderMarker(
        extractor_marker=body_extractor_marker,
        field_extractor_marker=field_extractor_marker,
        openapi_marker=body_openapi_marker,
        openapi_field_marker=openapi_field_marker,
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
    body_extractor = files.BodyExtractorMarker(
        media_type=media_type,
        enforce_media_type=enforce_media_type,
        consume=consume,
    )
    field_extractor_marker = files.FieldExtractorMarker()
    openapi_body_marker = files.BodyOpenAPIMarker(
        description=description,
        examples=examples,
        media_type=media_type,
        format=format,
        include_in_schema=include_in_schema,
    )
    openapi_field_marker = files.FieldOpenAPIMarker(
        media_type=media_type,
        format=format,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=body_extractor,
        field_extractor_marker=field_extractor_marker,
        openapi_marker=openapi_body_marker,
        openapi_field_marker=openapi_field_marker,
    )


def FormEncodedField(
    *,
    alias: typing.Optional[str] = None,
    style: openapi_models.FormDataStyles = "form",
    explode: bool = True,
    include_in_schema: bool = True,
) -> FormFieldMarker:
    extractor_marker = forms.FormEncodedFieldExtractorMarker(
        alias=alias,
        style=style,
        explode=explode,
    )
    openapi_marker = forms.FormEncodedOpenAPIMarker(
        alias=alias,
        style=style,
        explode=explode,
        include_in_schema=include_in_schema,
    )
    return FormFieldMarker(
        extractor_marker=extractor_marker,
        openapi_marker=openapi_marker,
    )


def FormField(
    *,
    alias: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> FormFieldMarker:
    extractor = forms.FieldExtractorMarker(alias=alias, repeated=False)
    openapi = forms.FieldOpenAPIMarker(
        alias=alias,
        include_in_schema=include_in_schema,
        repeated=False,
    )
    return FormFieldMarker(
        extractor_marker=extractor,
        openapi_marker=openapi,
    )


def RepeatedFormField(
    *,
    alias: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> FormFieldMarker:
    extractor = forms.FieldExtractorMarker(alias=alias, repeated=True)
    openapi = forms.FieldOpenAPIMarker(
        alias=alias,
        include_in_schema=include_in_schema,
        repeated=True,
    )
    return FormFieldMarker(
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
    body_extractor_marker = forms.BodyExtractorMarker(
        media_type="application/x-www-form-urlencoded",
        enforce_media_type=enforce_media_type,
    )
    body_openapi_marker = forms.BodyOpenAPIMarker(
        description=description,
        examples=examples,
        media_type="application/x-www-form-urlencoded",
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=body_extractor_marker,
        field_extractor_marker=None,
        openapi_marker=body_openapi_marker,
        openapi_field_marker=None,
    )


def Multipart(
    *,
    enforce_media_type: bool = True,
    examples: typing.Optional[typing.Dict[str, Example]] = None,
    description: typing.Optional[str] = None,
    include_in_schema: bool = True,
) -> param_dependants.BodyBinderMarker:
    body_extractor_marker = forms.BodyExtractorMarker(
        media_type="multipart/form-data",
        enforce_media_type=enforce_media_type,
    )
    body_openapi_marker = forms.BodyOpenAPIMarker(
        description=description,
        examples=examples,
        media_type="multipart/form-data",
        include_in_schema=include_in_schema,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=body_extractor_marker,
        field_extractor_marker=None,
        openapi_marker=body_openapi_marker,
        openapi_field_marker=None,
    )


def ContentTypeDiscriminatedBody(
    *,
    description: typing.Optional[str] = None,
) -> param_dependants.BodyBinderMarker:
    extractor = discriminated.BodyExtractorMarker()
    openapi = discriminated.BodyOpenAPIMarker(
        description=description,
    )
    return param_dependants.BodyBinderMarker(
        extractor_marker=extractor,
        field_extractor_marker=None,
        openapi_marker=openapi,
        openapi_field_marker=None,
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
