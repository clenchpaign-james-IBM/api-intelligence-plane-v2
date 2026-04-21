"""Vendor-neutral transactional log models for API Intelligence Plane.

Represents raw transactional events from API gateways for analytics and drill-down.
Supports multiple vendors: webMethods, Kong, Apigee, etc.

Note: Aggregated metrics are stored separately in metric.py (Metric model).
This file contains only raw transactional event data (TransactionalLog, ExternalCall).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Type of analytics event."""

    TRANSACTIONAL = "transactional"
    LIFECYCLE = "lifecycle"
    POLICY_VIOLATION = "policy_violation"
    THREAT_PROTECTION = "threat_protection"
    ERROR = "error"


class EventStatus(str, Enum):
    """Status of the transactional event."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class ErrorOrigin(str, Enum):
    """Origin of the error in the request flow."""

    BACKEND = "backend"  # Upstream/native service
    GATEWAY = "gateway"  # Gateway processing
    CLIENT = "client"  # Client/application
    NETWORK = "network"  # Network issues


class CacheStatus(str, Enum):
    """Response caching status."""

    HIT = "hit"
    MISS = "miss"
    BYPASS = "bypass"
    DISABLED = "disabled"


class ExternalCallType(str, Enum):
    """Type of external call made during request processing."""

    BACKEND_SERVICE = "backend_service"  # Main upstream service
    ROUTING = "routing"  # Load balancing/routing
    POLICY_ENFORCEMENT = "policy_enforcement"  # Policy validation
    AUTHENTICATION = "authentication"  # Auth service
    RATE_LIMITING = "rate_limiting"  # Rate limit check
    CUSTOM = "custom"


class ExternalCall(BaseModel):
    """External call made during request processing."""

    call_type: ExternalCallType = Field(..., description="Type of external call")
    url: str = Field(..., description="URL of the external service")
    method: Optional[str] = Field(None, description="HTTP method used")
    start_time: int = Field(..., description="Call start timestamp (epoch ms)")
    end_time: int = Field(..., description="Call end timestamp (epoch ms)")
    duration_ms: int = Field(..., description="Call duration in milliseconds")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    success: bool = Field(..., description="Whether call succeeded")

    # Optional details
    request_size: Optional[int] = Field(None, description="Request size in bytes")
    response_size: Optional[int] = Field(None, description="Response size in bytes")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class TransactionalLog(BaseModel):
    """
    Vendor-neutral transactional log for API requests.

    Represents a complete API transaction including request/response details,
    timing metrics, and external service calls. Works across all gateway vendors.

    Design Principles:
    1. Core fields are vendor-neutral
    2. Vendor-specific details in vendor_metadata
    3. Consistent naming (snake_case, no aliases)
    4. Standard HTTP concepts (not vendor-specific)

    Attributes:
        id: Unique identifier
        event_type: Type of event
        timestamp: Event timestamp (epoch ms)

        # API Identification
        api_id: API identifier
        api_name: API name
        api_version: API version
        operation: Operation/endpoint name

        # Request Details
        http_method: HTTP method
        request_path: Request path
        request_headers: Request headers
        request_payload: Request payload
        request_size: Request size in bytes
        query_parameters: Query parameters

        # Response Details
        status_code: HTTP status code
        response_headers: Response headers
        response_payload: Response payload
        response_size: Response size in bytes

        # Client Information
        client_id: Client/application identifier
        client_name: Client/application name
        client_ip: Client IP address
        user_agent: User agent string

        # Timing Metrics
        total_time_ms: Total request time
        gateway_time_ms: Gateway processing time
        backend_time_ms: Backend service time

        # Status and Tracking
        status: Request status (success/failure)
        correlation_id: Correlation ID for tracking
        session_id: Session identifier
        trace_id: Distributed tracing ID

        # Caching
        cache_status: Response caching status

        # Backend Service Details
        backend_url: Backend service URL
        backend_method: HTTP method to backend
        backend_request_headers: Headers sent to backend
        backend_response_headers: Headers from backend

        # Error Information
        error_origin: Origin of error if failed
        error_message: Error message
        error_code: Error code

        # External Calls
        external_calls: List of external calls made

        # Gateway Information
        gateway_id: Gateway instance identifier
        gateway_node: Gateway node/server identifier

        # Vendor-Specific Extensions
        vendor_metadata: Vendor-specific fields

        # Metadata
        created_at: Record creation timestamp
    """

    # ========================================================================
    # Core Identification
    # ========================================================================
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    event_type: EventType = Field(..., description="Type of analytics event")
    timestamp: int = Field(..., description="Event timestamp (epoch milliseconds)")

    # ========================================================================
    # API Identification
    # ========================================================================
    api_id: str = Field(..., description="API identifier")
    api_name: str = Field(..., description="API name")
    api_version: str = Field(..., description="API version")
    operation: str = Field(..., description="Operation/endpoint name")

    # ========================================================================
    # Request Details
    # ========================================================================
    http_method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    request_path: str = Field(..., description="Request path")
    request_headers: dict[str, str] = Field(
        default_factory=dict, description="Request headers"
    )
    request_payload: Optional[str] = Field(None, description="Request payload")
    request_size: int = Field(default=0, description="Request size in bytes")
    query_parameters: dict[str, Any] = Field(
        default_factory=dict, description="Query parameters"
    )

    # ========================================================================
    # Response Details
    # ========================================================================
    status_code: int = Field(..., description="HTTP status code")
    response_headers: dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    response_payload: Optional[str] = Field(None, description="Response payload")
    response_size: int = Field(default=0, description="Response size in bytes")

    # ========================================================================
    # Client Information
    # ========================================================================
    client_id: str = Field(..., description="Client/application identifier")
    client_name: Optional[str] = Field(None, description="Client/application name")
    client_ip: str = Field(..., description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")

    # ========================================================================
    # Timing Metrics (all in milliseconds)
    # ========================================================================
    total_time_ms: int = Field(..., description="Total request time (ms)")
    gateway_time_ms: int = Field(..., description="Gateway processing time (ms)")
    backend_time_ms: int = Field(..., description="Backend service time (ms)")

    # ========================================================================
    # Status and Tracking
    # ========================================================================
    status: EventStatus = Field(..., description="Request status")
    correlation_id: str = Field(..., description="Correlation ID for tracking")
    session_id: Optional[str] = Field(None, description="Session identifier")
    trace_id: Optional[str] = Field(None, description="Distributed tracing ID")

    # ========================================================================
    # Caching
    # ========================================================================
    cache_status: CacheStatus = Field(..., description="Response caching status")

    # ========================================================================
    # Backend Service Details
    # ========================================================================
    backend_url: str = Field(..., description="Backend service URL")
    backend_method: Optional[str] = Field(None, description="HTTP method to backend")
    backend_request_headers: dict[str, str] = Field(
        default_factory=dict, description="Headers sent to backend"
    )
    backend_response_headers: dict[str, str] = Field(
        default_factory=dict, description="Headers from backend"
    )

    # ========================================================================
    # Error Information
    # ========================================================================
    error_origin: Optional[ErrorOrigin] = Field(
        None, description="Origin of error if request failed"
    )
    error_message: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")

    # ========================================================================
    # External Calls
    # ========================================================================
    external_calls: list[ExternalCall] = Field(
        default_factory=list, description="External calls made during processing"
    )

    # ========================================================================
    # Gateway Information
    # ========================================================================
    gateway_id: str = Field(..., description="Gateway instance identifier")
    gateway_node: Optional[str] = Field(
        None, description="Gateway node/server identifier"
    )

    # ========================================================================
    # Vendor-Specific Extensions
    # ========================================================================
    vendor_metadata: Optional[dict[str, Any]] = Field(
        None, description="Vendor-specific metadata (webMethods, Kong, Apigee, etc.)"
    )

    # ========================================================================
    # Metadata
    # ========================================================================
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "event_type": "transactional",
                "timestamp": 1775710369360,
                "api_id": "dfe828c7-ea69-4399-8807-83e07be8ebc6",
                "api_name": "User Service API",
                "api_version": "1.0.0",
                "operation": "/users/{id}",
                "http_method": "GET",
                "request_path": "/api/v1/users/123",
                "status_code": 200,
                "client_id": "mobile-app",
                "client_name": "Mobile App",
                "client_ip": "192.168.1.100",
                "total_time_ms": 459,
                "gateway_time_ms": 317,
                "backend_time_ms": 142,
                "status": "success",
                "correlation_id": "abc-123-def-456",
                "cache_status": "miss",
                "backend_url": "http://backend:8080/users/123",
                "gateway_id": "gateway-01",
            }
        }



# Made with Bob