"""Metric model for API Intelligence Plane.

Represents time-series performance metrics for APIs.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EndpointMetric(BaseModel):
    """Per-endpoint metrics breakdown."""

    endpoint: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    response_time_p50: float = Field(..., ge=0, description="50th percentile (ms)")
    response_time_p95: float = Field(..., ge=0, description="95th percentile (ms)")
    response_time_p99: float = Field(..., ge=0, description="99th percentile (ms)")
    error_rate: float = Field(..., ge=0, le=1, description="Error rate (0-1)")
    request_count: int = Field(..., ge=0, description="Total requests")


class Metric(BaseModel):
    """Metric entity representing time-series performance metrics.

    Attributes:
        id: Unique identifier (UUID v4)
        api_id: Reference to API
        gateway_id: Reference to Gateway
        timestamp: Metric timestamp
        response_time_p50: 50th percentile (ms)
        response_time_p95: 95th percentile (ms)
        response_time_p99: 99th percentile (ms)
        error_rate: Error rate (0-1)
        error_count: Total errors
        request_count: Total requests
        throughput: Requests per second
        availability: Availability %
        status_codes: Status code distribution
        endpoint_metrics: Per-endpoint metrics (optional)
        metadata: Additional metrics
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    api_id: UUID = Field(..., description="Reference to API")
    gateway_id: UUID = Field(..., description="Reference to Gateway")
    timestamp: datetime = Field(..., description="Metric timestamp")
    response_time_p50: float = Field(..., ge=0, description="50th percentile (ms)")
    response_time_p95: float = Field(..., ge=0, description="95th percentile (ms)")
    response_time_p99: float = Field(..., ge=0, description="99th percentile (ms)")
    error_rate: float = Field(..., ge=0, le=1, description="Error rate (0-1)")
    error_count: int = Field(..., ge=0, description="Total errors")
    request_count: int = Field(..., gt=0, description="Total requests")
    throughput: float = Field(..., ge=0, description="Requests per second")
    availability: float = Field(..., ge=0, le=100, description="Availability %")
    status_codes: dict[str, int] = Field(
        ..., description="Status code distribution (code: count)"
    )
    endpoint_metrics: Optional[list[EndpointMetric]] = Field(
        None, description="Per-endpoint metrics"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metrics")

    @field_validator("response_time_p95")
    @classmethod
    def validate_p95(cls, v: float, info) -> float:
        """Validate p95 >= p50."""
        if "response_time_p50" in info.data and v < info.data["response_time_p50"]:
            raise ValueError("response_time_p95 must be >= response_time_p50")
        return v

    @field_validator("response_time_p99")
    @classmethod
    def validate_p99(cls, v: float, info) -> float:
        """Validate p99 >= p95 >= p50."""
        if "response_time_p95" in info.data and v < info.data["response_time_p95"]:
            raise ValueError("response_time_p99 must be >= response_time_p95")
        return v

    @field_validator("error_rate")
    @classmethod
    def validate_error_rate(cls, v: float, info) -> float:
        """Validate error_rate = error_count / request_count."""
        if "error_count" in info.data and "request_count" in info.data:
            expected_rate = info.data["error_count"] / info.data["request_count"]
            # Allow small floating point differences
            if abs(v - expected_rate) > 0.001:
                raise ValueError(
                    f"error_rate ({v}) must equal error_count / request_count ({expected_rate})"
                )
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate timestamp is within last 90 days (retention policy)."""
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        if v < ninety_days_ago:
            raise ValueError("timestamp must be within last 90 days")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "api_id": "550e8400-e29b-41d4-a716-446655440001",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-03-09T15:00:00Z",
                "response_time_p50": 45.2,
                "response_time_p95": 120.5,
                "response_time_p99": 250.0,
                "error_rate": 0.02,
                "error_count": 30,
                "request_count": 1500,
                "throughput": 25.0,
                "availability": 99.95,
                "status_codes": {
                    "200": 1450,
                    "404": 20,
                    "500": 10,
                    "503": 20,
                },
                "endpoint_metrics": [
                    {
                        "endpoint": "/users/{id}",
                        "method": "GET",
                        "response_time_p50": 40.0,
                        "response_time_p95": 100.0,
                        "response_time_p99": 200.0,
                        "error_rate": 0.01,
                        "request_count": 800,
                    }
                ],
            }
        }

# Made with Bob
