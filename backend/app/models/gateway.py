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
    """Supported gateway vendors."""

    NATIVE = "native"
    WEBMETHODS = "webmethods"
    KONG = "kong"
    APIGEE = "apigee"
    AWS = "aws"
    AZURE = "azure"
    CUSTOM = "custom"


class ConnectionType(str, Enum):
    """Gateway connection methods."""

    REST_API = "rest_api"
    GRPC = "grpc"
    GRAPHQL = "graphql"


class GatewayStatus(str, Enum):
    """Gateway connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class GatewayCredentials(BaseModel):
    """Gateway authentication credentials (encrypted at rest)."""

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

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Gateway name")
    vendor: GatewayVendor = Field(..., description="Gateway vendor")
    version: Optional[str] = Field(None, description="Gateway version")
    base_url: HttpUrl = Field(
        ..., description="Gateway base URL (e.g., https://gateway.example.com:5555) used to construct endpoints for APIs, Policies, and PolicyActions"
    )
    transactional_logs_url: Optional[HttpUrl] = Field(
        None,
        description="Separate endpoint for transactional logs (if different from connection_url)",
    )
    connection_type: ConnectionType = Field(..., description="Connection method")
    base_url_credentials: Optional[GatewayCredentials] = Field(
        None, description="Authentication credentials for base_url (None for no authentication)"
    )
    transactional_logs_credentials: Optional[GatewayCredentials] = Field(
        None,
        description="Authentication credentials for transactional_logs_url (None for no authentication)",
    )
    capabilities: list[str] = Field(
        ..., min_length=1, description="Supported features"
    )
    status: GatewayStatus = Field(
        default=GatewayStatus.DISCONNECTED, description="Connection status"
    )
    last_connected_at: Optional[datetime] = Field(
        None, description="Last successful connection"
    )
    last_error: Optional[str] = Field(
        None, max_length=1000, description="Last error message"
    )
    api_count: int = Field(default=0, ge=0, description="Number of APIs")
    metrics_enabled: bool = Field(default=True, description="Metrics collection enabled")
    security_scanning_enabled: bool = Field(
        default=True, description="Security scanning enabled"
    )
    rate_limiting_enabled: bool = Field(
        default=False, description="Rate limiting enabled"
    )
    configuration: Optional[dict[str, Any]] = Field(
        None, description="Vendor-specific config"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("base_url", "transactional_logs_url")
    @classmethod
    def validate_urls(cls, v: Optional[HttpUrl]) -> Optional[HttpUrl]:
        """Validate URLs use HTTPS (except localhost)."""
        if v:
            url_str = str(v)
            if not url_str.startswith("https://") and "localhost" not in url_str:
                raise ValueError("URLs must use HTTPS (except localhost)")
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
