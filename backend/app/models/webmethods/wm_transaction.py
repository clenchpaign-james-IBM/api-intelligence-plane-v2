"""Transactional log model for API Intelligence Plane.

Represents a transactional event from an API Gateway, including request/response
details, timing metrics, external calls, and error information.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Type of event."""

    TRANSACTIONAL = "Transactional"
    LIFECYCLE = "Lifecycle"
    POLICY = "Policy"
    ERROR = "Error"


class RequestStatus(str, Enum):
    """Request status."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    REJECTED = "REJECTED"


class CachedResponseType(str, Enum):
    """Cache status."""

    CACHED = "Cached"
    NOT_CACHED = "Not-Cached"
    PARTIAL = "Partial"


class ErrorOrigin(str, Enum):
    """Origin of error."""

    NATIVE = "NATIVE"
    GATEWAY = "GATEWAY"
    POLICY = "POLICY"
    BACKEND = "BACKEND"


class ExternalCallType(str, Enum):
    """Type of external call."""

    NATIVE_SERVICE_CALL = "NATIVE_SERVICE_CALL"
    REST_API_CALL = "REST_API_CALL"
    SOAP_SERVICE_CALL = "SOAP_SERVICE_CALL"
    DATABASE_CALL = "DATABASE_CALL"


class ExternalCall(BaseModel):
    """External call details."""

    externalCallType: ExternalCallType = Field(..., description="Type of external call")
    externalURL: str = Field(..., description="External service URL")
    callStartTime: int = Field(..., description="Call start timestamp (epoch ms)")
    callEndTime: int = Field(..., description="Call end timestamp (epoch ms)")
    callDuration: int = Field(..., description="Call duration in milliseconds")
    responseCode: str = Field(default="", description="HTTP response code")


class TransactionalLog(BaseModel):
    """Transactional log entity representing an API Gateway transaction.

    Attributes:
        id: Unique identifier (UUID v4)
        eventType: Type of event
        sourceGateway: Source gateway identifier
        tenantId: Tenant identifier
        creationDate: Event creation timestamp (epoch ms)
        apiName: API name
        apiVersion: API version
        apiId: API identifier (UUID)
        totalTime: Total request time in milliseconds
        sessionId: Session identifier
        providerTime: Backend provider time in milliseconds
        gatewayTime: Gateway processing time in milliseconds
        applicationName: Client application name
        applicationIp: Client IP address
        applicationId: Client application identifier
        status: Request status
        reqPayload: Request payload
        resPayload: Response payload
        totalDataSize: Total data size in bytes
        responseCode: HTTP response code
        cachedResponse: Cache status
        operationName: API operation/endpoint
        httpMethod: HTTP method
        requestHeaders: Request headers
        responseHeaders: Response headers
        queryParameters: Query parameters
        correlationID: Correlation identifier
        errorOrigin: Origin of error (if any)
        nativeRequestHeaders: Native service request headers
        nativeReqPayload: Native service request payload
        nativeResponseHeaders: Native service response headers
        nativeResPayload: Native service response payload
        nativeHttpMethod: Native service HTTP method
        nativeURL: Native service URL
        serverID: Gateway server identifier
        externalCalls: List of external calls
        sourceGatewayNode: Gateway node identifier
        callbackRequest: Whether this is a callback request
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    eventType: EventType = Field(..., description="Type of event")
    sourceGateway: str = Field(..., description="Source gateway identifier")
    tenantId: str = Field(..., description="Tenant identifier")
    creationDate: int = Field(..., description="Event creation timestamp (epoch ms)")
    apiName: str = Field(..., description="API name")
    apiVersion: str = Field(..., description="API version")
    apiId: UUID = Field(..., description="API identifier")
    totalTime: int = Field(..., ge=0, description="Total request time in milliseconds")
    sessionId: str = Field(..., description="Session identifier")
    providerTime: int = Field(..., ge=0, description="Backend provider time in milliseconds")
    gatewayTime: int = Field(..., ge=0, description="Gateway processing time in milliseconds")
    applicationName: str = Field(..., description="Client application name")
    applicationIp: str = Field(..., description="Client IP address")
    applicationId: str = Field(..., description="Client application identifier")
    status: RequestStatus = Field(..., description="Request status")
    reqPayload: str = Field(default="", description="Request payload")
    resPayload: str = Field(default="", description="Response payload")
    totalDataSize: int = Field(..., ge=0, description="Total data size in bytes")
    responseCode: str = Field(..., description="HTTP response code")
    cachedResponse: CachedResponseType = Field(..., description="Cache status")
    operationName: str = Field(..., description="API operation/endpoint")
    httpMethod: str = Field(..., description="HTTP method")
    requestHeaders: dict[str, str] = Field(default_factory=dict, description="Request headers")
    responseHeaders: dict[str, str] = Field(default_factory=dict, description="Response headers")
    queryParameters: dict[str, Any] = Field(
        default_factory=dict, description="Query parameters"
    )
    correlationID: str = Field(..., description="Correlation identifier")
    errorOrigin: Optional[ErrorOrigin] = Field(None, description="Origin of error (if any)")
    nativeRequestHeaders: dict[str, str] = Field(
        default_factory=dict, description="Native service request headers"
    )
    nativeReqPayload: str = Field(default="", description="Native service request payload")
    nativeResponseHeaders: dict[str, str] = Field(
        default_factory=dict, description="Native service response headers"
    )
    nativeResPayload: str = Field(default="", description="Native service response payload")
    nativeHttpMethod: str = Field(..., description="Native service HTTP method")
    nativeURL: str = Field(..., description="Native service URL")
    serverID: str = Field(..., description="Gateway server identifier")
    externalCalls: list[ExternalCall] = Field(
        default_factory=list, description="List of external calls"
    )
    sourceGatewayNode: str = Field(..., description="Gateway node identifier")
    callbackRequest: bool = Field(default=False, description="Whether this is a callback request")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("apiId", mode="before")
    @classmethod
    def validate_api_id(cls, v: Any) -> UUID:
        """Convert string UUID to UUID object."""
        if isinstance(v, str):
            return UUID(v)
        return v

    @field_validator("httpMethod", "nativeHttpMethod")
    @classmethod
    def validate_http_method(cls, v: str) -> str:
        """Normalize HTTP method to uppercase."""
        return v.upper()

    @field_validator("totalTime")
    @classmethod
    def validate_total_time(cls, v: int, info) -> int:
        """Validate total time equals provider time + gateway time."""
        if "providerTime" in info.data and "gatewayTime" in info.data:
            expected = info.data["providerTime"] + info.data["gatewayTime"]
            # Allow small variance due to rounding
            if abs(v - expected) > 10:
                raise ValueError(
                    f"totalTime ({v}ms) should approximately equal "
                    f"providerTime + gatewayTime ({expected}ms)"
                )
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "eventType": "Transactional",
                "sourceGateway": "APIGateway",
                "tenantId": "default",
                "creationDate": 1775710369360,
                "apiName": "Swagger Petstore - OpenAPI 3.0",
                "apiVersion": "1.0.27",
                "apiId": "dfe828c7-ea69-4399-8807-83e07be8ebc6",
                "totalTime": 459,
                "sessionId": "1ea972ca650f49819160411b4ebcec94",
                "providerTime": 142,
                "gatewayTime": 317,
                "applicationName": "Unknown",
                "applicationIp": "172.19.0.1",
                "applicationId": "Unknown",
                "status": "FAILURE",
                "reqPayload": "",
                "resPayload": '{"Exception":"API Gateway encountered an error..."}',
                "totalDataSize": 459,
                "responseCode": "500",
                "cachedResponse": "Not-Cached",
                "operationName": "/pet/findByStatus",
                "httpMethod": "GET",
                "requestHeaders": {
                    "Authorization": "**************",
                    "User-Agent": "insomnia/12.5.0",
                    "Host": "192.168.88.4:5555",
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "responseHeaders": {"Content-Type": "application/json"},
                "queryParameters": {},
                "correlationID": "APIGW:2256217d-9f3e-4b35-9e22-eb4b80b10bea:907",
                "errorOrigin": "NATIVE",
                "nativeRequestHeaders": {
                    "Authorization": "**************",
                    "User-Agent": "insomnia/12.5.0",
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "nativeReqPayload": "",
                "nativeResponseHeaders": {},
                "nativeResPayload": "",
                "nativeHttpMethod": "GET",
                "nativeURL": "https://petstore3.swagger.io/api/v3/pet/findByStatus",
                "serverID": "192.168.88.4:5555",
                "externalCalls": [
                    {
                        "externalCallType": "NATIVE_SERVICE_CALL",
                        "externalURL": "https://petstore3.swagger.io/api/v3/pet/findByStatus",
                        "callStartTime": 1775710369612,
                        "callEndTime": 1775710369752,
                        "callDuration": 140,
                        "responseCode": "",
                    }
                ],
                "sourceGatewayNode": "172.19.0.2",
                "callbackRequest": False,
            }
        }


# Made with Bob