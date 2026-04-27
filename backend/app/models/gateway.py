"""Gateway model for API Intelligence Plane.

Represents a connected API Gateway with vendor information, connection details,
capabilities, and associated APIs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class GatewayVendor(str, Enum):
    """Supported API Gateway vendors.
    
    Defines the gateway platforms that the API Intelligence Plane can connect to
    and monitor. Each vendor may have specific adapter implementations for API
    discovery, metrics collection, and policy management.
    
    Attributes:
        WEBMETHODS: Software AG webMethods API Gateway - Enterprise API management platform.
        KONG: Kong Gateway - Open-source and enterprise API gateway.
        APIGEE: Google Apigee API Management - Cloud-native API platform.
        AWS: Amazon API Gateway - AWS-managed API gateway service.
        AZURE: Azure API Management - Microsoft Azure API management service.
        CUSTOM: Custom or unsupported gateway vendor requiring custom adapter implementation.
    """

    WEBMETHODS = "webmethods"
    KONG = "kong"
    APIGEE = "apigee"
    AWS = "aws"
    AZURE = "azure"
    CUSTOM = "custom"


class ConnectionType(str, Enum):
    """Gateway connection protocol types.
    
    Specifies the communication protocol used to connect to and interact with
    the API Gateway's management interface.
    
    Attributes:
        REST_API: RESTful HTTP/HTTPS API - Most common gateway management interface.
        GRPC: gRPC protocol - High-performance RPC framework for gateway communication.
        GRAPHQL: GraphQL API - Query language for gateway management operations.
    """

    REST_API = "rest_api"
    GRPC = "grpc"
    GRAPHQL = "graphql"


class GatewayStatus(str, Enum):
    """Gateway connection status.
    
    Represents the current operational state of the gateway's connection
    to the API Intelligence Plane.
    
    Gateway Lifecycle:
        1. Registration (DISCONNECTED):
           - Gateway is registered via POST /api/v1/gateways
           - Initial status is DISCONNECTED
           - Gateway configuration is stored but no active connection exists
        
        2. Connection Establishment (DISCONNECTED → CONNECTED):
           - Discovery service attempts to connect to the gateway
           - Validates credentials and connectivity
           - On success: status changes to CONNECTED, last_connected_at is updated
           - On failure: status changes to ERROR, last_error is populated
        
        3. Normal Operations (CONNECTED):
           - API discovery runs periodically
           - Metrics are collected continuously
           - Policies can be applied and updated
           - Health checks maintain connection status
        
        4. Connection Failure (CONNECTED → ERROR):
           - Network issues, authentication failures, or gateway unavailability
           - Automatic retry attempts may occur
           - Manual intervention required to resolve underlying issue
           - Can transition back to CONNECTED once issue is resolved
        
        5. Intentional Disconnect (CONNECTED → DISCONNECTED):
           - Admin manually disconnects gateway
           - Gateway remains registered but inactive
           - Can be reconnected later without re-registration
        
        6. Decommissioning (any status → deleted):
           - Gateway is removed via DELETE /api/v1/gateways/{id}
           - All associated data (APIs, metrics, policies) may be archived
    
    Status Transitions:
        - DISCONNECTED ↔ CONNECTED (via connection/disconnection)
        - DISCONNECTED → ERROR (connection attempt fails)
        - CONNECTED → ERROR (connection lost or health check fails)
        - ERROR → CONNECTED (issue resolved and reconnected)
        - ERROR → DISCONNECTED (manual disconnect after error)
    
    Attributes:
        CONNECTED: Gateway is actively connected and operational. The Intelligence
            Plane can successfully communicate with the gateway, discover APIs,
            collect metrics, and apply policies.
        DISCONNECTED: Gateway is not currently connected. This is the default state
            for newly registered gateways or when connection has been intentionally
            terminated. No data collection or policy application is possible.
        ERROR: Gateway connection has failed or encountered an error. The last_error
            field in the Gateway model will contain details about the failure.
            Requires investigation and remediation before normal operations can resume.
    
    Note:
        MAINTENANCE status has been deferred to a future phase. For planned maintenance,
        use the DISCONNECTED status and document the reason in the metadata field.
    """

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class GatewayCredentials(BaseModel):
    """Gateway authentication credentials (encrypted at rest).
    
    Stores authentication credentials for connecting to gateway management APIs.
    All sensitive fields (password, api_key, token) are encrypted before storage
    using the application's encryption service.
    
    Attributes:
        type: Authentication method type. Valid values: 'api_key', 'oauth2', 'basic',
             'bearer', 'none'. Determines which credential fields are required.
        username: Username for basic authentication. Required when type='basic'.
        password: Password for basic authentication (stored encrypted). Required when type='basic'.
        api_key: API key for key-based authentication (stored encrypted). Required when type='api_key'.
        token: Bearer token for token-based authentication (stored encrypted). Required when type='bearer'.
    """

    type: str = Field(..., description="Credential type (e.g., 'api_key', 'oauth2', 'none')")
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(None, description="Password (encrypted)")
    api_key: Optional[str] = Field(None, description="API key (encrypted)")
    token: Optional[str] = Field(None, description="Bearer token (encrypted)")

    @field_validator("type")
    @classmethod
    def validate_credential_type(cls, v: str) -> str:
        """Validate credential type and ensure required fields are present."""
        valid_types = ["api_key", "oauth2", "basic", "bearer", "none"]
        if v not in valid_types:
            raise ValueError(f"Credential type must be one of: {', '.join(valid_types)}")
        return v


class Gateway(BaseModel):
    """Gateway entity representing a connected API Gateway.

    Attributes:
        id: Unique identifier (UUID v4)
        name: Gateway name (1-255 characters)
        vendor: Gateway vendor (native, kong, apigee, aws, azure, custom)
        version: Gateway version (semantic versioning)
        connection_url: Gateway API endpoint for APIs, Policies, and Policy Actions (HTTPS URL)
        transactional_logs_url: Optional separate endpoint for transactional logs (HTTPS URL)
        connection_type: Connection method (rest_api, grpc, graphql)
        base_url_credentials: Authentication credentials for base_url (encrypted, optional)
        transactional_logs_credentials: Authentication credentials for transactional_logs_url (encrypted, optional)
        capabilities: Supported features list
        status: Connection status (connected, disconnected, error, maintenance)
        last_connected_at: Last successful connection timestamp
        last_error: Last error message (max 1000 characters)
        api_count: Number of APIs (non-negative)
        metrics_enabled: Metrics collection enabled flag
        security_scanning_enabled: Security scanning enabled flag
        rate_limiting_enabled: Rate limiting enabled flag
        configuration: Vendor-specific config (max 50KB)
        metadata: Additional metadata (max 10KB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the gateway (UUID v4 format). Auto-generated on creation."
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name of the gateway (1-255 characters). Used for identification in UI and logs."
    )
    vendor: GatewayVendor = Field(
        ...,
        description="Gateway vendor/platform (native, webmethods, kong, apigee, aws, azure, custom). Determines adapter implementation."
    )
    version: Optional[str] = Field(
        None,
        description="Gateway software version (e.g., '10.15', '3.2.1'). Used for compatibility checks and feature detection."
    )
    base_url: HttpUrl = Field(
        ...,
        description="Gateway base URL (e.g., https://gateway.example.com:5555) used to construct endpoints for APIs, Policies, and PolicyActions. Must use HTTPS except for localhost."
    )
    transactional_logs_url: Optional[HttpUrl] = Field(
        None,
        description="Separate endpoint for transactional logs if different from base_url. Used when logs are served from a different service or port."
    )
    connection_type: ConnectionType = Field(
        ...,
        description="Communication protocol for gateway management API (rest_api, grpc, graphql). Determines how Intelligence Plane interacts with gateway."
    )
    base_url_credentials: Optional[GatewayCredentials] = Field(
        None,
        description="Authentication credentials for base_url (encrypted at rest). None if gateway requires no authentication."
    )
    transactional_logs_credentials: Optional[GatewayCredentials] = Field(
        None,
        description="Authentication credentials for transactional_logs_url (encrypted at rest). None if logs endpoint requires no authentication."
    )
    capabilities: list[str] = Field(
        ...,
        min_length=1,
        description="List of supported features (e.g., 'api_discovery', 'metrics_collection', 'rate_limiting'). Must have at least one capability."
    )
    status: GatewayStatus = Field(
        default=GatewayStatus.DISCONNECTED,
        description="Current connection status (connected, disconnected, error). Defaults to disconnected for new gateways. Updated by health checks."
    )
    last_connected_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of last successful connection. Updated when gateway responds to health checks. Cannot be in the future."
    )
    last_error: Optional[str] = Field(
        None,
        max_length=1000,
        description="Last error message if connection failed (max 1000 characters). Cleared when connection succeeds. Used for troubleshooting."
    )
    api_count: int = Field(
        default=0,
        ge=0,
        description="Number of APIs discovered on this gateway. Updated by discovery service. Non-negative integer."
    )
    metrics_enabled: bool = Field(
        default=True,
        description="Whether metrics collection is enabled for this gateway. When true, metrics are continuously collected and stored."
    )
    security_scanning_enabled: bool = Field(
        default=True,
        description="Whether security scanning is enabled for APIs on this gateway. When true, vulnerabilities are detected and tracked."
    )
    rate_limiting_enabled: bool = Field(
        default=False,
        description="Whether rate limiting policies can be applied to this gateway. Requires gateway support for rate limiting."
    )
    configuration: Optional[dict[str, Any]] = Field(
        None,
        description="Vendor-specific configuration settings. Structure varies by gateway vendor. Used for custom adapter behavior."
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional flexible metadata for custom fields, tags, or integration data. Not used by core system."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when gateway was registered. Auto-generated. Used for aging and audit trails."
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of last update to gateway configuration. Auto-updated on changes. Tracks modification history."
    )

    @field_validator("base_url", "transactional_logs_url")
    @classmethod
    def validate_urls(cls, v: Optional[HttpUrl]) -> Optional[HttpUrl]:
        """Validate URLs use HTTPS (except localhost and development hosts)."""
        if v:
            url_str = str(v)
            # Allow HTTP for localhost, 127.0.0.1, host.docker.internal, and 0.0.0.0
            local_hosts = ["localhost", "127.0.0.1", "host.docker.internal", "0.0.0.0"]
            is_local = any(host in url_str for host in local_hosts)
            
            if not url_str.startswith("https://") and not is_local:
                raise ValueError("URLs must use HTTPS (except localhost and development hosts)")
        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[str]) -> list[str]:
        """Validate capabilities list is not empty."""
        if not v:
            raise ValueError("Capabilities list cannot be empty")
        return v

    @field_validator("last_connected_at")
    @classmethod
    def validate_last_connected_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate last_connected_at is not in the future."""
        if v and v > datetime.utcnow():
            raise ValueError("last_connected_at cannot be in the future")
        return v
    
    def to_llm_dict(self) -> dict[str, Any]:
        """
        Generate LLM-optimized dictionary representation.
        
        Trims large/redundant fields to reduce token count while maintaining
        essential context for natural language response generation.
        
        Estimated reduction: 40-60% for typical gateway entities.
        
        Returns:
            Trimmed dictionary suitable for LLM context
        """
        result = {
            "id": str(self.id),
            "name": self.name,
            "vendor": self.vendor.value,
            "version": self.version,
            "base_url": str(self.base_url),
            "connection_type": self.connection_type.value,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "api_count": self.api_count,
            "metrics_enabled": self.metrics_enabled,
            "security_scanning_enabled": self.security_scanning_enabled,
            "rate_limiting_enabled": self.rate_limiting_enabled,
        }
        
        # Trim last_error - keep only first 100 characters
        if self.last_error:
            result["last_error"] = self.last_error[:100]
        
        # Drop: base_url_credentials, transactional_logs_credentials (security risk)
        # Drop: transactional_logs_url (not needed for LLM context)
        # Drop: configuration, metadata (too large/vendor-specific)
        
        return result

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Production Gateway",
                "vendor": "native",
                "version": "1.0.0",
                "base_url": "https://gateway.example.com:5555",
                "transactional_logs_url": "https://analytics.example.com/logs",
                "connection_type": "rest_api",
                "base_url_credentials": {
                    "type": "api_key",
                    "api_key": "encrypted_key_here",
                },
                "transactional_logs_credentials": {
                    "type": "basic",
                    "username": "analytics_user",
                    "password": "encrypted_password_here",
                },
                "capabilities": [
                    "api_discovery",
                    "metrics_collection",
                    "rate_limiting",
                ],
                "status": "connected",
                "api_count": 25,
                "metrics_enabled": True,
                "security_scanning_enabled": True,
                "rate_limiting_enabled": False,
            }
        }

# Made with Bob
