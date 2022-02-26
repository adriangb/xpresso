from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Union

from pydantic import BaseConfig, BaseModel, Extra, Field
from pydantic.networks import AnyUrl

try:
    import email_validator  # type: ignore # noqa: F401
    from pydantic import EmailStr
except ImportError:  # pragma: no cover
    EmailStr = str  # type: ignore


from xpresso._utils.compat import Annotated, Literal


class FrozenBaseModel(BaseModel):
    class Config(BaseConfig):
        frozen = True


ParameterLocations = Literal["header", "path", "query", "cookie"]
PathParamStyles = Literal["simple", "label", "matrix"]
QueryParamStyles = Literal["form", "spaceDelimited", "pipeDelimited", "deepObject"]
HeaderParamStyles = Literal["simple"]
CookieParamStyles = Literal["form"]
FormDataStyles = QueryParamStyles

Extension = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class Contact(FrozenBaseModel):
    name: Optional[str] = None
    url: Optional[AnyUrl] = None
    email: Optional[EmailStr] = None


class License(FrozenBaseModel):
    name: str
    url: Optional[AnyUrl] = None


class Info(FrozenBaseModel):
    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None

    class Config(FrozenBaseModel.Config):
        extra = Extra.allow  # for extensions


class ServerVariable(FrozenBaseModel):
    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None


class Server(FrozenBaseModel):
    url: Union[AnyUrl, str]
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None


class Reference(FrozenBaseModel):
    ref: Annotated[str, Field(alias="$ref")]


class Discriminator(FrozenBaseModel):
    propertyName: str
    mapping: Optional[Dict[str, str]] = None


class XML(FrozenBaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    prefix: Optional[str] = None
    attribute: Optional[bool] = None
    wrapped: Optional[bool] = None


class ExternalDocumentation(FrozenBaseModel):
    url: AnyUrl
    description: Optional[str] = None


class Schema(FrozenBaseModel):
    ref: Annotated[Optional[str], Field(alias="$ref")] = None
    title: Optional[str] = None
    multipleOf: Optional[float] = None
    maximum: Optional[float] = None
    exclusiveMaximum: Optional[float] = None
    minimum: Optional[float] = None
    exclusiveMinimum: Optional[float] = None
    maxLength: Annotated[Optional[int], Field(ge=0)] = None
    minLength: Annotated[Optional[int], Field(ge=0)] = None
    pattern: Optional[str] = None
    maxItems: Annotated[Optional[int], Field(ge=0)] = None
    minItems: Annotated[Optional[int], Field(ge=0)] = None
    uniqueItems: Optional[bool] = None
    maxProperties: Annotated[Optional[int], Field(ge=0)] = None
    minProperties: Annotated[Optional[int], Field(ge=0)] = None
    required: Optional[List[str]] = None
    enum: Optional[List[Any]] = None
    type: Optional[str] = None
    allOf: Optional[List[Schema]] = None
    oneOf: Optional[List[Schema]] = None
    anyOf: Optional[List[Schema]] = None
    not_: Annotated[Optional[Schema], Field(alias="not")] = None
    items: Optional[Union[Schema, List[Schema]]] = None
    properties: Optional[Dict[str, Schema]] = None
    additionalProperties: Optional[Union[Schema, Reference, bool]] = None
    description: Optional[str] = None
    format: Optional[str] = None
    default: Any = None
    nullable: Optional[bool] = None
    discriminator: Optional[Discriminator] = None
    readOnly: Optional[bool] = None
    writeOnly: Optional[bool] = None
    xml: Optional[XML] = None
    externalDocs: Optional[ExternalDocumentation] = None
    deprecated: Optional[bool] = None
    example: Optional[Any] = None
    examples: Optional[Examples] = None


class Example(FrozenBaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Any = None
    external_value: Annotated[Optional[str], Field(alias="externalValue")]


Examples = Mapping[str, Union[Example, Reference]]


class Encoding(FrozenBaseModel):
    contentType: Optional[str] = None
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    style: Optional[str] = None
    explode: Optional[bool] = None


class MediaType(FrozenBaseModel):
    schema_: Optional[Union[Schema, Reference]] = Field(alias="schema")
    examples: Optional[Examples] = None
    encoding: Optional[Dict[str, Encoding]] = None


class ParameterBase(FrozenBaseModel):
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    # Serialization rules for simple scenarios
    style: Optional[str] = None
    explode: Optional[bool] = None
    schema_: Annotated[Optional[Union[Schema, Reference]], Field(alias="schema")]
    examples: Optional[Examples] = None
    # Serialization rules for more complex scenarios
    content: Optional[Dict[str, MediaType]] = None


class ConcreteParameter(ParameterBase):
    name: str
    in_: ParameterLocations


class Header(ConcreteParameter):
    in_: Annotated[Literal["header"], Field(alias="in")] = "header"
    style: HeaderParamStyles = "simple"
    explode: bool = False


class Query(ConcreteParameter):
    in_: Annotated[Literal["query"], Field(alias="in")] = "query"
    style: QueryParamStyles = "form"
    explode: bool = True


class Path(ConcreteParameter):
    in_: Annotated[Literal["path"], Field(alias="in")] = "path"
    style: PathParamStyles = "simple"
    explode: bool = False
    required: Literal[True] = True


class Cookie(ConcreteParameter):
    in_: Annotated[Literal["cookie"], Field(alias="in")] = "cookie"
    style: CookieParamStyles = "form"
    explode: bool = True


Parameter = Union[Query, Header, Cookie, Path]


class RequestBody(FrozenBaseModel):
    content: Dict[str, MediaType]
    description: Optional[str] = None
    required: Optional[bool] = None


class Link(FrozenBaseModel):
    operationRef: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[Dict[str, str]] = None
    requestBody: Optional[str] = None
    description: Optional[str] = None
    server: Optional[Server] = None


class ResponseHeader(FrozenBaseModel):
    description: Optional[str] = None
    deprecated: Optional[bool] = None
    # Serialization rules for simple scenarios
    style: HeaderParamStyles = "simple"
    explode: bool = False
    schema_: Optional[Union[Schema, Reference]] = Field(None, alias="schema")
    examples: Optional[Examples] = None
    # Serialization rules for more complex scenarios
    content: Optional[Dict[str, MediaType]] = None


class Response(FrozenBaseModel):
    description: str
    headers: Optional[Dict[str, Union[ResponseHeader, Reference]]] = None
    content: Optional[Dict[str, MediaType]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None


class Operation(FrozenBaseModel):
    responses: Dict[str, Union[Response, Reference]]
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None
    operationId: Optional[str] = None
    parameters: Optional[List[Union[ConcreteParameter, Reference]]] = None
    requestBody: Optional[Union[RequestBody, Reference]] = None
    # Using Any for Specification Extensions
    callbacks: Optional[Dict[str, Union[Dict[str, PathItem], Reference]]] = None
    deprecated: Optional[bool] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    servers: Optional[List[Server]] = None

    class Config(FrozenBaseModel.Config):
        extra = Extra.allow  # for extensions


class PathItem(FrozenBaseModel):
    ref: Annotated[Optional[str], Field(alias="$ref")] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    delete: Optional[Operation] = None
    options: Optional[Operation] = None
    head: Optional[Operation] = None
    patch: Optional[Operation] = None
    trace: Optional[Operation] = None
    servers: Optional[List[Server]] = None
    parameters: Optional[List[Union[Parameter, Reference]]] = None

    class Config(FrozenBaseModel.Config):
        extra = Extra.allow  # for extensions


SecuritySchemeName = Literal["apiKey", "http", "oauth2", "openIdConnect"]


class SecurityBase(FrozenBaseModel):
    type: SecuritySchemeName
    description: Optional[str] = None


APIKeyLocation = Literal["query", "header", "cookie"]


class APIKey(SecurityBase):
    name: str
    in_: Annotated[APIKeyLocation, Field(alias="in")]
    type: Literal["apiKey"] = "apiKey"


class HTTPBase(SecurityBase):
    scheme: str
    type: Literal["http"] = "http"


class HTTPBearer(HTTPBase):
    scheme = "bearer"
    bearerFormat: Optional[str] = None


class OAuthFlow(FrozenBaseModel):
    refreshUrl: Optional[AnyUrl] = None
    scopes: Optional[Mapping[str, str]] = Field(default_factory=dict)  # type: ignore

    def __hash__(self) -> int:  # type: ignore  # for Pylance
        return hash((self.__class__, self.refreshUrl))


class OAuthFlowImplicit(OAuthFlow):
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlow):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlow):
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    authorizationUrl: str
    tokenUrl: str


class OAuthFlows(FrozenBaseModel):
    implicit: Optional[OAuthFlowImplicit] = None
    password: Optional[OAuthFlowPassword] = None
    clientCredentials: Optional[OAuthFlowClientCredentials] = None
    authorizationCode: Optional[OAuthFlowAuthorizationCode] = None


class OAuth2(SecurityBase):
    flows: OAuthFlows
    type: Literal["oauth2"] = "oauth2"


class OpenIdConnect(SecurityBase):
    openIdConnectUrl: str
    type: Literal["openIdConnect"] = "openIdConnect"


SecurityScheme = Union[APIKey, HTTPBase, OAuth2, OpenIdConnect, HTTPBearer]


class Components(FrozenBaseModel):
    schemas: Optional[Dict[str, Union[Schema, Reference]]] = None
    responses: Optional[Dict[str, Union[Response, Reference]]] = None
    parameters: Optional[Dict[str, Union[Parameter, Reference]]] = None
    examples: Optional[Examples] = None
    requestBodies: Optional[Dict[str, Union[RequestBody, Reference]]] = None
    headers: Optional[Dict[str, Union[Header, Reference]]] = None
    securitySchemes: Optional[Dict[str, Union[SecurityScheme, Reference]]] = None
    links: Optional[Dict[str, Union[Link, Reference]]] = None
    callbacks: Optional[Dict[str, Union[Dict[str, PathItem], Reference]]] = None


class Tag(FrozenBaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocumentation] = None


class OpenAPI(FrozenBaseModel):
    openapi: str
    info: Info
    paths: Dict[str, Union[PathItem, Extension]] = Field(default_factory=dict)
    servers: Optional[List[Server]] = None
    # Using Any for Specification Extensions
    components: Optional[Components] = None
    security: Optional[List[Dict[str, List[str]]]] = None
    tags: Optional[List[Tag]] = None
    externalDocs: Optional[ExternalDocumentation] = None


Schema.update_forward_refs()
Operation.update_forward_refs()
Encoding.update_forward_refs()
