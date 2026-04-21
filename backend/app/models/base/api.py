"""Vendor-neutral API model for API Intelligence Plane.

Represents a discovered API with comprehensive metadata, supporting multiple
gateway vendors (webMethods, Kong, Apigee, etc.) while maintaining intelligence-first design.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

# Import structured policy configurations
from .policy_configs import (
    RateLimitConfig,
    AuthenticationConfig,
    AuthorizationConfig,
    CachingConfig,
    CorsConfig,
    ValidationConfig,
    DataMaskingConfig,
    TransformationConfig,
    LoggingConfig,
    TlsConfig,
    CompressionConfig,
    PolicyConfigType,
)


# ============================================================================
# Enumerations
# ============================================================================

class AuthenticationType(str, Enum):
    """API authentication mechanisms (vendor-neutral)."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    MTLS = "mtls"
    CUSTOM = "custom"


class DiscoveryMethod(str, Enum):
    """How the API was discovered."""

    REGISTERED = "registered"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    LOG_ANALYSIS = "log_analysis"
    GATEWAY_SYNC = "gateway_sync"


class APIStatus(str, Enum):
    """Current API status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class APIType(str, Enum):
    """API protocol type."""

    REST = "REST"
    SOAP = "SOAP"
    GRAPHQL = "GRAPHQL"
    WEBSOCKET = "WEBSOCKET"
    GRPC = "GRPC"
    ODATA = "ODATA"


class MaturityState(str, Enum):
    """API maturity/lifecycle state."""

    BETA = "Beta"
    TEST = "Test"
    PRODUCTIVE = "Productive"
    DEPRECATED = "Deprecated"
    RETIRED = "Retired"


class PolicyActionType(str, Enum):
    """Standard policy action types across vendors."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    CACHING = "caching"
    LOGGING = "logging"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    CORS = "cors"
    DATA_MASKING = "data_masking"
    COMPRESSION = "compression"
    TLS = "tls"
    CUSTOM = "custom"


# ============================================================================
# API Definition (OpenAPI/Swagger Structure)
# ============================================================================

class APIDefinition(BaseModel):
    """
    Vendor-neutral API definition supporting OpenAPI/Swagger specifications.
    Can be extended with vendor-specific fields via vendor_extensions.
    """

    type: str = Field(..., description="API type (REST, SOAP, etc.)")
    version: Optional[str] = Field(None, description="API specification version")

    # OpenAPI/Swagger fields
    openapi_spec: Optional[dict[str, Any]] = Field(
        None, description="Full OpenAPI/Swagger specification"
    )
    swagger_version: Optional[str] = Field(None, description="Swagger version if applicable")

    # Basic definition
    base_path: str = Field(..., description="Base path for API")
    paths: Optional[dict[str, Any]] = Field(None, description="API paths/endpoints")
    schemas: Optional[dict[str, Any]] = Field(None, description="Data schemas/models")

    # Security definitions
    security_schemes: Optional[dict[str, Any]] = Field(
        None, description="Security scheme definitions"
    )

    # Vendor-specific extensions
    vendor_extensions: Optional[dict[str, Any]] = Field(
        None, description="Vendor-specific API definition extensions (x-* fields)"
    )


# ============================================================================
# Endpoints
# ============================================================================

class EndpointParameter(BaseModel):
    """API endpoint parameter definition."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (path, query, header, body)")
    data_type: str = Field(..., description="Data type (string, integer, etc.)")
    required: bool = Field(default=False, description="Whether parameter is required")
    description: Optional[str] = Field(None, description="Parameter description")


class Endpoint(BaseModel):
    """API endpoint definition."""

    path: str = Field(..., description="Endpoint path (e.g., /users/{id})")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    description: Optional[str] = Field(None, description="Endpoint description")
    parameters: list[EndpointParameter] = Field(
        default_factory=list, description="Endpoint parameters"
    )
    response_codes: list[int] = Field(
        default_factory=list, description="Expected response codes"
    )
    # Native endpoint details (for gateway routing)
    connection_timeout: Optional[int] = Field(None, description="Connection timeout (ms)")
    read_timeout: Optional[int] = Field(None, description="Read timeout (ms)")


# ============================================================================
# Policy Actions (Vendor-Neutral)
# ============================================================================

class PolicyAction(BaseModel):
    """
    Vendor-neutral policy action configuration.
    
    Uses structured type-safe configurations (PolicyConfigType) for all policy actions.
    Dict-based configurations are no longer supported.
    
    Examples:
        # Structured config (required)
        PolicyAction(
            action_type=PolicyActionType.RATE_LIMITING,
            config=RateLimitConfig(requests_per_minute=1000)
        )
        
        PolicyAction(
            action_type=PolicyActionType.AUTHENTICATION,
            config=AuthenticationConfig(auth_type="oauth2")
        )
    """

    action_type: PolicyActionType = Field(..., description="Type of policy action")
    enabled: bool = Field(default=True, description="Whether action is enabled")
    stage: Optional[str] = Field(
        None, description="Execution stage (request, response, error)"
    )

    # Policy configuration - structured configs only
    config: Optional[PolicyConfigType] = Field(
        None,
        description="Policy-specific configuration (structured config required)"
    )

    # Vendor-specific configuration
    vendor_config: Optional[dict[str, Any]] = Field(
        None, description="Vendor-specific policy configuration"
    )

    # Metadata
    name: Optional[str] = Field(None, description="Policy action name")
    description: Optional[str] = Field(None, description="Policy action description")
    
    @model_validator(mode='before')
    @classmethod
    def validate_and_convert_config(cls, data: Any) -> Any:
        """
        Convert dict-based configs to structured configs during deserialization.
        This allows OpenSearch to return dicts that get converted to proper Pydantic models.
        """
        if isinstance(data, dict):
            config = data.get("config")
            if config is not None and isinstance(config, dict):
                action_type = data.get("action_type")
                
                # Map action types to their config classes
                config_type_map = {
                    PolicyActionType.RATE_LIMITING: RateLimitConfig,
                    PolicyActionType.AUTHENTICATION: AuthenticationConfig,
                    PolicyActionType.AUTHORIZATION: AuthorizationConfig,
                    PolicyActionType.CACHING: CachingConfig,
                    PolicyActionType.CORS: CorsConfig,
                    PolicyActionType.VALIDATION: ValidationConfig,
                    PolicyActionType.DATA_MASKING: DataMaskingConfig,
                    PolicyActionType.TRANSFORMATION: TransformationConfig,
                    PolicyActionType.LOGGING: LoggingConfig,
                    PolicyActionType.TLS: TlsConfig,
                    PolicyActionType.COMPRESSION: CompressionConfig,
                }
                
                # Convert dict to appropriate structured config
                config_class = config_type_map.get(action_type)
                if config_class:
                    try:
                        data["config"] = config_class(**config)
                    except Exception as e:
                        raise ValueError(
                            f"Failed to convert dict config to {config_class.__name__} "
                            f"for action_type '{action_type}': {e}"
                        )
        return data
    
    @field_validator("config")
    @classmethod
    def validate_config_type(cls, v, info):
        """
        Validate config matches action_type.
        Only structured configs are allowed.
        """
        if v is None:
            return v
        
        # Validate type matches action_type
        action_type = info.data.get("action_type")
        config_type_map = {
            PolicyActionType.RATE_LIMITING: RateLimitConfig,
            PolicyActionType.AUTHENTICATION: AuthenticationConfig,
            PolicyActionType.AUTHORIZATION: AuthorizationConfig,
            PolicyActionType.CACHING: CachingConfig,
            PolicyActionType.CORS: CorsConfig,
            PolicyActionType.VALIDATION: ValidationConfig,
            PolicyActionType.DATA_MASKING: DataMaskingConfig,
            PolicyActionType.TRANSFORMATION: TransformationConfig,
            PolicyActionType.LOGGING: LoggingConfig,
            PolicyActionType.TLS: TlsConfig,
            PolicyActionType.COMPRESSION: CompressionConfig,
        }
        
        expected_type = config_type_map.get(action_type)
        if expected_type and not isinstance(v, expected_type):
            raise ValueError(
                f"Config type {type(v).__name__} does not match "
                f"action_type {action_type}. Expected {expected_type.__name__}"
            )
        
        return v


# ============================================================================
# Ownership and Organization
# ============================================================================

class OwnershipInfo(BaseModel):
    """API ownership information."""

    team: Optional[str] = Field(None, description="Owning team")
    contact: Optional[str] = Field(None, description="Contact email")
    repository: Optional[str] = Field(None, description="Source repository URL")
    organization: Optional[str] = Field(None, description="Organization name")
    department: Optional[str] = Field(None, description="Department name")


# ============================================================================
# Versioning
# ============================================================================

class VersionInfo(BaseModel):
    """API version information."""

    current_version: str = Field(..., description="Current API version")
    previous_version: Optional[str] = Field(None, description="Previous version")
    next_version: Optional[str] = Field(None, description="Next planned version")
    system_version: int = Field(default=1, description="Internal system version counter")
    version_history: Optional[list[str]] = Field(None, description="Version history")


# ============================================================================
# Publishing and Deployment
# ============================================================================

class PublishingInfo(BaseModel):
    """API publishing and portal information."""

    published_portals: list[str] = Field(
        default_factory=list, description="List of portals where API is published"
    )
    published_to_registry: bool = Field(
        default=False, description="Whether published to service registry"
    )
    catalog_name: Optional[str] = Field(None, description="Catalog name")
    catalog_id: Optional[str] = Field(None, description="Catalog identifier")


class DeploymentInfo(BaseModel):
    """API deployment information."""

    environment: str = Field(..., description="Deployment environment (dev, staging, prod)")
    gateway_endpoints: dict[str, str] = Field(
        default_factory=dict, description="Gateway endpoint URLs by environment"
    )
    deployed_at: Optional[datetime] = Field(None, description="Deployment timestamp")
    deployment_status: Optional[str] = Field(None, description="Deployment status")


# ============================================================================
# Intelligence Fields (API Intelligence Plane Specific)
# ============================================================================

class IntelligenceMetadata(BaseModel):
    """
    Intelligence-specific metadata for API analysis.
    These fields are computed by the intelligence plane, not from gateway.
    """

    # Discovery
    is_shadow: bool = Field(default=False, description="Shadow API detection flag")
    discovery_method: DiscoveryMethod = Field(..., description="How API was discovered")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
    last_seen_at: datetime = Field(..., description="Last activity timestamp")

    # Health and performance
    health_score: float = Field(..., ge=0, le=100, description="Computed health score (0-100)")

    # Risk assessment
    risk_score: Optional[float] = Field(
        None, ge=0, le=100, description="Computed risk score (0-100)"
    )
    security_score: Optional[float] = Field(
        None, ge=0, le=100, description="Computed security score (0-100)"
    )

    # Compliance
    compliance_status: Optional[dict[str, bool]] = Field(
        None, description="Compliance status by standard (e.g., {'PCI-DSS': true})"
    )

    # Usage patterns
    usage_trend: Optional[str] = Field(
        None, description="Usage trend (increasing, stable, decreasing)"
    )

    # Predictions
    has_active_predictions: bool = Field(
        default=False, description="Whether API has active failure predictions"
    )

    @field_validator("last_seen_at")
    @classmethod
    def validate_last_seen_at(cls, v: datetime, info) -> datetime:
        """Validate last_seen_at >= discovered_at."""
        if "discovered_at" in info.data and v < info.data["discovered_at"]:
            raise ValueError("last_seen_at must be >= discovered_at")
        return v


# ============================================================================
# Main API Model (Vendor-Neutral)
# ============================================================================

class API(BaseModel):
    """
    Vendor-neutral API model for API Intelligence Plane.

    Design Principles:
    1. Core fields are vendor-neutral and required for intelligence
    2. Vendor-specific details stored in vendor_metadata
    3. Intelligence fields separated in intelligence_metadata
    4. Metrics stored separately (not embedded) - referenced by api_id
    5. Policy actions use vendor-neutral types with vendor_config extension
    6. Supports OpenAPI/Swagger via api_definition

    Attributes:
        id: Unique identifier (UUID v4)
        gateway_id: Reference to parent Gateway
        name: API name
        display_name: Human-readable display name
        description: API description
        version_info: Version information
        type: API protocol type (REST, SOAP, etc.)
        maturity_state: Lifecycle state
        groups: API groups/categories
        tags: Categorization tags
        api_definition: Full API definition (OpenAPI/Swagger)
        endpoints: List of API endpoints
        methods: HTTP methods supported
        authentication_type: Auth mechanism
        authentication_config: Auth configuration
        policy_actions: Applied policy actions (vendor-neutral)
        ownership: Ownership information
        publishing: Publishing and portal information
        deployments: Deployment information
        intelligence_metadata: Intelligence-specific fields
        status: Current status
        is_active: Whether API is active
        vendor_metadata: Vendor-specific fields
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    # ========================================================================
    # Core Identification
    # ========================================================================
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Reference to parent Gateway")

    # ========================================================================
    # Basic Metadata
    # ========================================================================
    name: str = Field(..., min_length=1, max_length=255, description="API name")
    display_name: Optional[str] = Field(None, description="Human-readable display name")
    description: Optional[str] = Field(None, description="API description")
    icon: Optional[str] = Field(None, description="API icon URL or identifier")

    # ========================================================================
    # Versioning
    # ========================================================================
    version_info: VersionInfo = Field(..., description="Version information")

    # ========================================================================
    # Type and Classification
    # ========================================================================
    type: APIType = Field(default=APIType.REST, description="API protocol type")
    maturity_state: Optional[MaturityState] = Field(
        None, description="API maturity/lifecycle state"
    )
    groups: list[str] = Field(default_factory=list, description="API groups/categories")
    tags: list[str] = Field(
        default_factory=list, max_length=20, description="Categorization tags"
    )

    # ========================================================================
    # Base Path (for querying and routing)
    # ========================================================================
    base_path: str = Field(..., description="Base URL path for API routing")

    # ========================================================================
    # API Definition (OpenAPI/Swagger)
    # ========================================================================
    api_definition: Optional[APIDefinition] = Field(
        None, description="Full API definition (OpenAPI/Swagger)"
    )

    # ========================================================================
    # Endpoints
    # ========================================================================
    endpoints: list[Endpoint] = Field(..., min_length=1, description="API endpoints")
    methods: list[str] = Field(..., min_length=1, description="HTTP methods supported")

    # ========================================================================
    # Authentication
    # ========================================================================
    authentication_type: AuthenticationType = Field(..., description="Auth mechanism")
    authentication_config: Optional[dict[str, Any]] = Field(
        None, description="Auth configuration (encrypted if contains secrets)"
    )

    # ========================================================================
    # Policy Actions (Vendor-Neutral)
    # ========================================================================
    policy_actions: Optional[list[PolicyAction]] = Field(
        None, description="Applied policy actions with configurations"
    )

    # ========================================================================
    # Ownership
    # ========================================================================
    ownership: Optional[OwnershipInfo] = Field(None, description="Ownership information")

    # ========================================================================
    # Publishing and Deployment
    # ========================================================================
    publishing: Optional[PublishingInfo] = Field(
        None, description="Publishing and portal information"
    )
    deployments: Optional[list[DeploymentInfo]] = Field(
        None, description="Deployment information"
    )

    # ========================================================================
    # Intelligence Metadata (Computed by Intelligence Plane)
    # ========================================================================
    intelligence_metadata: IntelligenceMetadata = Field(
        ..., description="Intelligence-specific metadata"
    )

    # ========================================================================
    # Status
    # ========================================================================
    status: APIStatus = Field(default=APIStatus.ACTIVE, description="Current status")
    is_active: bool = Field(default=True, description="Whether API is active")

    # ========================================================================
    # Vendor-Specific Extensions
    # ========================================================================
    vendor_metadata: Optional[dict[str, Any]] = Field(
        None, description="Vendor-specific metadata (webMethods, Kong, Apigee, etc.)"
    )

    # ========================================================================
    # Timestamps
    # ========================================================================
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # ========================================================================
    # Validators
    # ========================================================================

    @field_validator("endpoints")
    @classmethod
    def validate_endpoints(cls, v: list[Endpoint]) -> list[Endpoint]:
        """Validate endpoints array is not empty."""
        if not v:
            raise ValueError("endpoints array cannot be empty")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate each tag is 1-50 characters."""
        for tag in v:
            if not (1 <= len(tag) <= 50):
                raise ValueError("Each tag must be 1-50 characters")
        return v

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, v: datetime, info) -> datetime:
        """Validate updated_at >= created_at."""
        if "created_at" in info.data and v < info.data["created_at"]:
            raise ValueError("updated_at must be >= created_at")
        return v

    def to_llm_dict(self) -> dict[str, Any]:
        """
        Generate LLM-optimized dictionary representation.
        
        Trims large/redundant fields to reduce token count while maintaining
        essential context for natural language response generation.
        
        Estimated reduction: 60-85% for typical API entities.
        
        Returns:
            Trimmed dictionary suitable for LLM context
        """
        # Start with essential fields
        result = {
            "id": str(self.id),
            "gateway_id": str(self.gateway_id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "base_path": self.base_path,
            "type": self.type.value,
            "maturity_state": self.maturity_state.value if self.maturity_state else None,
            "groups": self.groups,
            "tags": self.tags,
            "methods": self.methods,
            "authentication_type": self.authentication_type.value,
            "status": self.status.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        # Trim api_definition - keep only essential fields
        if self.api_definition:
            result["api_definition"] = {
                "type": self.api_definition.type,
                "version": self.api_definition.version,
                "base_path": self.api_definition.base_path,
            }
        
        # Trim endpoints - keep count and first 3 with simplified structure
        if self.endpoints:
            result["endpoints_count"] = len(self.endpoints)
            result["endpoints_sample"] = [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "description": ep.description,
                }
                for ep in self.endpoints[:3]
            ]
        
        # Trim policy_actions - keep only action_type, enabled, name
        if self.policy_actions:
            result["policy_actions"] = [
                {
                    "action_type": pa.action_type.value,
                    "enabled": pa.enabled,
                    "name": pa.name,
                }
                for pa in self.policy_actions
            ]
        
        # Trim ownership - keep only team and organization
        if self.ownership:
            result["ownership"] = {
                "team": self.ownership.team,
                "organization": self.ownership.organization,
            }
        
        # Trim publishing - keep only published_portals count
        if self.publishing:
            result["publishing"] = {
                "published_portals_count": len(self.publishing.published_portals),
            }
        
        # Trim deployments - keep count and environment names
        if self.deployments:
            result["deployments"] = {
                "count": len(self.deployments),
                "environments": [d.environment for d in self.deployments],
            }
        
        # Trim version_info - keep only current_version and system_version
        result["version_info"] = {
            "current_version": self.version_info.current_version,
            "system_version": self.version_info.system_version,
        }
        
        # Trim intelligence_metadata - keep most fields but simplify compliance_status
        if self.intelligence_metadata:
            result["intelligence_metadata"] = {
                "is_shadow": self.intelligence_metadata.is_shadow,
                "discovery_method": self.intelligence_metadata.discovery_method.value,
                "discovered_at": self.intelligence_metadata.discovered_at.isoformat(),
                "last_seen_at": self.intelligence_metadata.last_seen_at.isoformat(),
                "health_score": self.intelligence_metadata.health_score,
                "risk_score": self.intelligence_metadata.risk_score,
                "security_score": self.intelligence_metadata.security_score,
                "usage_trend": self.intelligence_metadata.usage_trend,
                "has_active_predictions": self.intelligence_metadata.has_active_predictions,
            }
            # Simplify compliance_status to just count
            if self.intelligence_metadata.compliance_status:
                result["intelligence_metadata"]["compliant_standards_count"] = sum(
                    1 for v in self.intelligence_metadata.compliance_status.values() if v
                )
        
        # Drop: authentication_config, vendor_metadata (too large/sensitive)
        
        return result

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "user-service-api",
                "display_name": "User Service API",
                "description": "User management REST API",
                "base_path": "/api/v1/users",
                "version_info": {
                    "current_version": "1.2.3",
                    "system_version": 1,
                },
                "type": "REST",
                "maturity_state": "Productive",
                "endpoints": [
                    {
                        "path": "/users/{id}",
                        "method": "GET",
                        "description": "Get user by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "type": "path",
                                "data_type": "integer",
                                "required": True,
                            }
                        ],
                        "response_codes": [200, 404, 500],
                    }
                ],
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "authentication_type": "bearer",
                "policy_actions": [
                    {
                        "action_type": "authentication",
                        "enabled": True,
                        "stage": "request",
                        "config": {"scheme": "bearer"},
                    },
                    {
                        "action_type": "rate_limiting",
                        "enabled": True,
                        "stage": "request",
                        "config": {"requests_per_minute": 1000},
                    },
                ],
                "intelligence_metadata": {
                    "is_shadow": False,
                    "discovery_method": "registered",
                    "discovered_at": "2026-03-09T10:00:00Z",
                    "last_seen_at": "2026-03-09T15:00:00Z",
                    "health_score": 95.5,
                    "has_active_predictions": False,
                },
                "status": "active",
                "is_active": True,
            }
        }


# Made with Bob
