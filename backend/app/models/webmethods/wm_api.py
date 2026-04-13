"""
Python Pydantic models converted from Java API Gateway classes.
IBM Confidential - Copyright 2024 IBM Corp.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field, ConfigDict

# Import policy action models
from .wm_policy_action import (
    EntryProtocolPolicy,
    EvaluatePolicy,
    AuthorizeUserPolicy,
    LogInvocationPolicy,
    ThrottlePolicy,
    ServiceResultCachePolicy,
    ValidateAPISpecPolicy,
    RequestDataMaskingPolicy,
    ResponseDataMaskingPolicy,
    CorsPolicy,
)


class VendorExtensions(BaseModel):
    """Base class for vendor extensions support."""
    vendor_extensions: Optional[Dict[str, Any]] = Field(None, alias="vendorExtensions")
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Contact(BaseModel):
    """Contact information for the API."""
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Licence(BaseModel):
    """License information for the API."""
    name: Optional[str] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Info(VendorExtensions):
    """Provides metadata about the API."""
    description: Optional[str] = None
    version: Optional[str] = None
    title: Optional[str] = None
    terms_of_service: Optional[str] = Field(None, alias="termsOfService")
    contact: Optional[Contact] = None
    license: Optional[Licence] = None
    
    model_config = ConfigDict(populate_by_name=True)


class ExternalDocs(VendorExtensions):
    """Additional external documentation."""
    description: Optional[str] = None
    url: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Tag(VendorExtensions):
    """Tag with additional metadata."""
    name: Optional[str] = None
    description: Optional[str] = None
    external_docs: Optional[ExternalDocs] = Field(None, alias="externalDocs")
    
    model_config = ConfigDict(populate_by_name=True)


class ServerVariable(BaseModel):
    """Server variable for URL templating."""
    enum: Optional[List[str]] = None
    default: Optional[str] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Server(VendorExtensions):
    """Server object providing connectivity information."""
    url: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Property(BaseModel):
    """Base property model."""
    type: Optional[str] = None
    format: Optional[str] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Schema(VendorExtensions):
    """Schema object for OpenAPI."""
    type: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    required: Optional[List[str]] = None
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Model(BaseModel):
    """Base model interface."""
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Parameter(BaseModel):
    """Parameter base interface."""
    in_: Optional[str] = Field(None, alias="in")
    access: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AbstractParameter(Parameter):
    """Abstract parameter implementation."""
    pass


class RequestBody(VendorExtensions):
    """Request body for operations."""
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    required: Optional[bool] = None
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True)


class ApiResponse(VendorExtensions):
    """API response base class."""
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True)


class Response(ApiResponse):
    """Response object."""
    schema_: Optional[Dict[str, Property]] = Field(None, alias="schema")
    examples: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(populate_by_name=True)


class MockedResponse(BaseModel):
    """Mocked response for testing."""
    status_code: Optional[str] = Field(None, alias="statusCode")
    body: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    model_config = ConfigDict(populate_by_name=True)


class MockedConditionsBasedCustomResponse(BaseModel):
    """Mocked conditions-based custom response."""
    condition: Optional[str] = None
    response: Optional[MockedResponse] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Callback(BaseModel):
    """Callback object."""
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Operation(VendorExtensions):
    """Operation on a path."""
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = Field(None, alias="operationId")
    schemes: Optional[List[str]] = None
    consumes: Optional[List[str]] = None
    produces: Optional[List[str]] = None
    parameters: Optional[List[Parameter]] = None
    responses: Optional[Dict[str, Response]] = None
    mocked_responses: Optional[Dict[str, MockedResponse]] = Field(None, alias="mockedResponses")
    mocked_conditions_based_custom_responses_list: Optional[List[MockedConditionsBasedCustomResponse]] = Field(
        None, alias="mockedConditionsBasedCustomResponsesList"
    )
    security: Optional[List[Any]] = None
    external_docs: Optional[ExternalDocs] = Field(None, alias="externalDocs")
    deprecated: Optional[bool] = None
    enabled: Optional[bool] = True
    scopes: Optional[List[str]] = None
    request_body: Optional[RequestBody] = Field(None, alias="requestBody")
    callbacks: Optional[Dict[str, Callback]] = None
    servers: Optional[List[Server]] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Path(VendorExtensions):
    """Path item with operations."""
    get: Optional[Operation] = None
    put: Optional[Operation] = None
    post: Optional[Operation] = None
    head: Optional[Operation] = None
    delete: Optional[Operation] = None
    patch: Optional[Operation] = None
    options: Optional[Operation] = None
    trace: Optional[Operation] = None
    parameters: Optional[List[Parameter]] = None
    request_body: Optional[RequestBody] = Field(None, alias="requestBody")
    scopes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = None
    security: Optional[List[Any]] = None
    enabled: Optional[bool] = True
    servers: Optional[List[Server]] = None
    ref: Optional[str] = Field(None, alias="$ref")
    summary: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class SecurityScheme(BaseModel):
    """Security scheme definition."""
    type: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    in_: Optional[str] = Field(None, alias="in")
    scheme: Optional[str] = None
    bearer_format: Optional[str] = Field(None, alias="bearerFormat")
    flows: Optional[Dict[str, Any]] = None
    open_id_connect_url: Optional[str] = Field(None, alias="openIdConnectUrl")
    
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Example(BaseModel):
    """Example object."""
    summary: Optional[str] = None
    description: Optional[str] = None
    value: Optional[Any] = None
    external_value: Optional[str] = Field(None, alias="externalValue")
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True)


class Header(BaseModel):
    """Header object."""
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = None
    schema_: Optional[Schema] = Field(None, alias="schema")
    
    model_config = ConfigDict(populate_by_name=True)


class Link(BaseModel):
    """Link object."""
    operation_ref: Optional[str] = Field(None, alias="operationRef")
    operation_id: Optional[str] = Field(None, alias="operationId")
    parameters: Optional[Dict[str, Any]] = None
    request_body: Optional[Any] = Field(None, alias="requestBody")
    description: Optional[str] = None
    server: Optional[Server] = None
    ref: Optional[str] = Field(None, alias="$ref")
    
    model_config = ConfigDict(populate_by_name=True)


class Components(VendorExtensions):
    """Components object holding reusable objects."""
    schemas: Optional[Dict[str, Schema]] = None
    responses: Optional[Dict[str, Response]] = None
    parameters: Optional[Dict[str, Parameter]] = None
    examples: Optional[Dict[str, Example]] = None
    request_bodies: Optional[Dict[str, RequestBody]] = Field(None, alias="requestBodies")
    headers: Optional[Dict[str, Header]] = None
    security_schemes: Optional[Dict[str, SecurityScheme]] = Field(None, alias="securitySchemes")
    links: Optional[Dict[str, Link]] = None
    callbacks: Optional[Dict[str, Callback]] = None
    
    model_config = ConfigDict(populate_by_name=True)


class SecurityRequirement(BaseModel):
    """Security requirement."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class APIDefinition(VendorExtensions):
    """REST API definition."""
    info: Optional[Info] = None
    host: Optional[str] = None
    base_path: Optional[str] = Field(None, alias="basePath")
    service_registry_display_name: Optional[str] = Field(None, alias="serviceRegistryDisplayName")
    tags: Optional[List[Tag]] = None
    schemes: Optional[List[str]] = None
    consumes: Optional[List[str]] = None
    produces: Optional[List[str]] = None
    security: Optional[List[Any]] = None
    paths: Optional[Dict[str, Path]] = None
    security_definitions: Optional[Dict[str, Any]] = Field(None, alias="securityDefinitions")
    definitions: Optional[Dict[str, Model]] = None
    parameters: Optional[Dict[str, Parameter]] = None
    base_uri_parameters: Optional[List[AbstractParameter]] = Field(None, alias="baseUriParameters")
    responses: Optional[Dict[str, Response]] = None
    external_docs: Optional[List[ExternalDocs]] = Field(None, alias="externalDocs")
    servers: Optional[List[Server]] = None
    components: Optional[Components] = None
    api_tags: Optional[List[str]] = Field(None, alias="apiTags")
    type: str = "rest"
    
    model_config = ConfigDict(populate_by_name=True)


class Scope(BaseModel):
    """OAuth scope definition."""
    name: Optional[str] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)


class Endpoint(BaseModel):
    """Native endpoint information."""
    uri: Optional[str] = None
    connection_timeout: Optional[int] = Field(None, alias="connectionTimeout")
    
    model_config = ConfigDict(populate_by_name=True)


class Policy(BaseModel):
    """Policy definition."""
    policy_id: Optional[str] = Field(None, alias="policyId")
    policy_name: Optional[str] = Field(None, alias="policyName")
    policy_description: Optional[str] = Field(None, alias="policyDescription")
    
    model_config = ConfigDict(populate_by_name=True)


class MockService(BaseModel):
    """Mock service configuration."""
    enabled: Optional[bool] = None
    mock_service_link: Optional[str] = Field(None, alias="mockServiceLink")
    
    model_config = ConfigDict(populate_by_name=True)


class APIDeploymentTypes(BaseModel):
    """API deployment types."""
    deployment_type: Optional[str] = Field(None, alias="deploymentType")
    deployment_id: Optional[str] = Field(None, alias="deploymentId")
    
    model_config = ConfigDict(populate_by_name=True)


class API(BaseModel):
    """
    Unified API model combining Gateway API metadata and REST API definition.
    Represents a complete API Gateway API with all metadata and definition.
    """
    # Core identification
    api_id: Optional[str] = Field(None, alias="apiId")
    doc_type: Optional[str] = Field("apis", alias="_docType")
    
    # API definition (RestAPI embedded)
    api_definition: Optional[APIDefinition] = Field(None, alias="apiDefinition")
    
    # Endpoints
    native_endpoint: Optional[Set[Endpoint]] = Field(None, alias="nativeEndpoint")
    
    # Basic metadata
    api_group_name: Optional[str] = Field(None, alias="apiGroupName")
    api_name: Optional[str] = Field(None, alias="apiName")
    api_display_name: Optional[str] = Field(None, alias="apiDisplayName")
    api_version: Optional[str] = Field(None, alias="apiVersion")
    api_endpoint_prefix: Optional[str] = Field(None, alias="apiEndpointPrefix")
    api_description: Optional[str] = Field(None, alias="apiDescription")
    api_icon: Optional[str] = Field(None, alias="apiIcon")
    
    # Status and classification
    maturity_state: Optional[str] = Field(None, alias="maturityState")
    api_groups: Optional[List[str]] = Field(None, alias="apiGroups")
    is_active: Optional[bool] = Field(None, alias="isActive")
    type: str = Field("REST", description="API type (REST, SOAP, WEBSOCKET, GRAPHQL, ODATA)")
    
    # Ownership and policies
    owner: Optional[str] = None
    policies: Optional[List[str]] = None
    
    # File references
    referenced_files: Optional[Dict[str, str]] = Field(None, alias="referencedFiles")
    root_file_name: Optional[str] = Field(None, alias="rootFileName")
    
    # OAuth and security
    o_auth2_scope_name: Optional[str] = Field(None, alias="oAuth2ScopeName")
    tracing_enabled: bool = Field(False, alias="tracingEnabled")
    scopes: Optional[List[Scope]] = None
    
    # Publishing and portals
    published_portals: Optional[List[str]] = Field(default_factory=list, alias="publishedPortals")
    published_to_registry: Optional[bool] = Field(None, alias="publishedToRegistry")
    
    # Timestamps
    creation_date: Optional[str] = Field(None, alias="creationDate")
    last_modified: Optional[str] = Field(None, alias="lastModified")
    
    # Versioning
    prev_version: Optional[str] = Field(None, alias="prevVersion")
    next_version: Optional[str] = Field(None, alias="nextVersion")
    system_version: int = Field(1, alias="systemVersion")
    
    # Provider information
    provider: Optional[str] = None
    centra_site_url: Optional[str] = Field(None, alias="centraSiteURL")
    portal_api_item_identifier: Optional[str] = Field(None, alias="portalApiItemIdentifier")
    
    # Mock service
    mock_service: Optional[MockService] = Field(None, alias="mockService")
    
    # Documentation
    api_documents: Optional[List[str]] = Field(None, alias="apiDocuments")
    gateway_endpoints: Optional[Dict[str, str]] = Field(None, alias="gatewayEndpoints")
    
    # Deployments
    deployments: Optional[List[APIDeploymentTypes]] = None
    
    # Catalog and organization
    catalog_name: Optional[str] = Field(None, alias="catalogName")
    p_org_name: Optional[str] = Field(None, alias="pOrgName")
    catalog_id: Optional[str] = Field(None, alias="catalogId")
    p_org_id: Optional[str] = Field(None, alias="pOrgId")
    migrated: Optional[bool] = None
    slugified_api_name: Optional[str] = Field(None, alias="slugifiedApiName")
    
    model_config = ConfigDict(populate_by_name=True)
