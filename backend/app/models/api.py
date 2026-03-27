"""API model for API Intelligence Plane.

Represents a discovered API with metadata, health metrics, security status,
and performance characteristics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class AuthenticationType(str, Enum):
    """API authentication mechanisms."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    CUSTOM = "custom"


class DiscoveryMethod(str, Enum):
    """How the API was discovered."""

    REGISTERED = "registered"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    LOG_ANALYSIS = "log_analysis"


class APIStatus(str, Enum):
    """Current API status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FAILED = "failed"


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


class CurrentMetrics(BaseModel):
    """Latest metrics snapshot for an API."""

    response_time_p50: float = Field(..., ge=0, description="50th percentile (ms)")
    response_time_p95: float = Field(..., ge=0, description="95th percentile (ms)")
    response_time_p99: float = Field(..., ge=0, description="99th percentile (ms)")
    error_rate: float = Field(..., ge=0, le=1, description="Error rate (0-1)")
    throughput: float = Field(..., ge=0, description="Requests per second")
    availability: float = Field(..., ge=0, le=100, description="Availability %")
    last_error: Optional[datetime] = Field(None, description="Last error timestamp")
    measured_at: datetime = Field(..., description="Measurement timestamp")

    @field_validator("response_time_p99")
    @classmethod
    def validate_percentiles(cls, v: float, info) -> float:
        """Validate p99 >= p95 >= p50."""
        if "response_time_p95" in info.data and v < info.data["response_time_p95"]:
            raise ValueError("response_time_p99 must be >= response_time_p95")
        return v


class OwnershipInfo(BaseModel):
    """API ownership information."""

    team: Optional[str] = Field(None, description="Owning team")
    contact: Optional[str] = Field(None, description="Contact email")
    repository: Optional[str] = Field(None, description="Source repository URL")


class SecurityPolicies(BaseModel):
    """Security policies applied to an API."""

    authentication_required: bool = Field(
        default=True, description="Whether authentication is required"
    )
    authorization_enabled: bool = Field(
        default=True, description="Whether authorization checks are enabled"
    )
    rate_limiting_enabled: bool = Field(
        default=False, description="Whether rate limiting is applied"
    )
    rate_limit_config: Optional[dict[str, Any]] = Field(
        None, description="Rate limit configuration (requests per minute, etc.)"
    )
    tls_enforced: bool = Field(
        default=True, description="Whether TLS/HTTPS is enforced"
    )
    tls_version: Optional[str] = Field(
        None, description="Minimum TLS version (e.g., 'TLS 1.2', 'TLS 1.3')"
    )
    cors_enabled: bool = Field(
        default=False, description="Whether CORS is enabled"
    )
    cors_config: Optional[dict[str, Any]] = Field(
        None, description="CORS configuration (allowed origins, methods, etc.)"
    )
    input_validation_enabled: bool = Field(
        default=False, description="Whether input validation is enforced"
    )
    output_sanitization_enabled: bool = Field(
        default=False, description="Whether output sanitization is applied"
    )
    logging_enabled: bool = Field(
        default=True, description="Whether security logging is enabled"
    )
    encryption_at_rest: bool = Field(
        default=False, description="Whether data encryption at rest is enabled"
    )
    waf_enabled: bool = Field(
        default=False, description="Whether Web Application Firewall is enabled"
    )
    ip_whitelisting_enabled: bool = Field(
        default=False, description="Whether IP whitelisting is applied"
    )
    allowed_ips: Optional[list[str]] = Field(
        None, description="List of whitelisted IP addresses/ranges"
    )
    api_key_rotation_enabled: bool = Field(
        default=False, description="Whether API key rotation is enforced"
    )
    key_rotation_days: Optional[int] = Field(
        None, description="API key rotation period in days"
    )
    compliance_standards: Optional[list[str]] = Field(
        None, description="Compliance standards (e.g., 'PCI-DSS', 'HIPAA', 'SOC2')"
    )
    last_policy_update: Optional[datetime] = Field(
        None, description="Last time policies were updated"
    )


class API(BaseModel):
    """API entity representing a discovered API.

    Attributes:
        id: Unique identifier (UUID v4)
        gateway_id: Reference to parent Gateway
        name: API name (1-255 characters)
        version: API version (semantic versioning)
        base_path: Base URL path
        endpoints: List of API endpoints (at least 1)
        methods: HTTP methods supported
        authentication_type: Auth mechanism
        authentication_config: Auth configuration (encrypted if contains secrets)
        ownership: Ownership information
        tags: Categorization tags (max 20, each 1-50 characters)
        is_shadow: Shadow API flag
        discovery_method: How API was found
        discovered_at: Discovery timestamp
        last_seen_at: Last activity timestamp
        status: Current status
        health_score: Overall health (0-100)
        current_metrics: Latest metrics snapshot
        metadata: Additional metadata (max 10KB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Reference to parent Gateway")
    name: str = Field(..., min_length=1, max_length=255, description="API name")
    version: Optional[str] = Field(None, description="API version")
    base_path: str = Field(..., description="Base URL path")
    endpoints: list[Endpoint] = Field(..., min_length=1, description="API endpoints")
    methods: list[str] = Field(..., min_length=1, description="HTTP methods supported")
    authentication_type: AuthenticationType = Field(..., description="Auth mechanism")
    authentication_config: Optional[dict[str, Any]] = Field(
        None, description="Auth configuration"
    )
    ownership: Optional[OwnershipInfo] = Field(None, description="Ownership information")
    tags: list[str] = Field(
        default_factory=list, max_length=20, description="Categorization tags"
    )
    is_shadow: bool = Field(default=False, description="Shadow API flag")
    discovery_method: DiscoveryMethod = Field(..., description="How API was found")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
    last_seen_at: datetime = Field(..., description="Last activity timestamp")
    status: APIStatus = Field(default=APIStatus.ACTIVE, description="Current status")
    health_score: float = Field(
        ..., ge=0, le=100, description="Overall health (0-100)"
    )
    current_metrics: CurrentMetrics = Field(..., description="Latest metrics snapshot")
    security_policies: Optional[SecurityPolicies] = Field(
        None, description="Security policies applied to this API"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("base_path")
    @classmethod
    def validate_base_path(cls, v: str) -> str:
        """Validate base_path starts with /."""
        if not v.startswith("/"):
            raise ValueError("base_path must start with /")
        return v

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

    @field_validator("last_seen_at")
    @classmethod
    def validate_last_seen_at(cls, v: datetime, info) -> datetime:
        """Validate last_seen_at >= discovered_at."""
        if "discovered_at" in info.data and v < info.data["discovered_at"]:
            raise ValueError("last_seen_at must be >= discovered_at")
        return v

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, v: datetime, info) -> datetime:
        """Validate updated_at >= created_at."""
        if "created_at" in info.data and v < info.data["created_at"]:
            raise ValueError("updated_at must be >= created_at")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "User Service API",
                "version": "1.2.3",
                "base_path": "/api/v1/users",
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
                "is_shadow": False,
                "discovery_method": "registered",
                "status": "active",
                "health_score": 95.5,
                "current_metrics": {
                    "response_time_p50": 45.2,
                    "response_time_p95": 120.5,
                    "response_time_p99": 250.0,
                    "error_rate": 0.02,
                    "throughput": 1500,
                    "availability": 99.95,
                    "measured_at": "2026-03-09T15:00:00Z",
                },
            }
        }

# Made with Bob
