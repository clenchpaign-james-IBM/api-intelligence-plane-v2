"""Vendor-neutral metrics model for API Intelligence Plane.

Represents aggregated time-series performance metrics for APIs.
Supports multiple gateway vendors with time-bucketed aggregation.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TimeBucket(str, Enum):
    """Time bucket for metric aggregation."""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"


class EndpointMetric(BaseModel):
    """Per-endpoint metrics breakdown."""

    endpoint: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    request_count: int = Field(..., ge=0, description="Total requests")
    success_count: int = Field(..., ge=0, description="Successful requests")
    failure_count: int = Field(..., ge=0, description="Failed requests")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage")
    response_time_avg: float = Field(..., ge=0, description="Average response time (ms)")
    response_time_p50: float = Field(..., ge=0, description="50th percentile (ms)")
    response_time_p95: float = Field(..., ge=0, description="95th percentile (ms)")
    response_time_p99: float = Field(..., ge=0, description="99th percentile (ms)")


class Metric(BaseModel):
    """
    Vendor-neutral aggregated time-series metrics.

    Represents aggregated performance metrics for a specific time bucket,
    derived from transactional logs. Supports drill-down analysis and
    works across all gateway vendors.

    Design Principles:
    1. Time-bucketed aggregation (1m, 5m, 1h, 1d)
    2. Comprehensive metrics (performance, cache, data transfer, status codes)
    3. Vendor-neutral naming (backend instead of provider/native)
    4. Optional per-endpoint breakdown
    5. Strong validation rules
    6. Vendor extensibility via vendor_metadata

    Attributes:
        id: Unique identifier
        gateway_id: Gateway instance identifier
        api_id: API identifier
        application_id: Application identifier (optional)
        operation: Specific operation/endpoint (optional)
        timestamp: Metric timestamp (start of time bucket)
        time_bucket: Time bucket size

        # Request Counts
        request_count: Total requests
        success_count: Successful requests
        failure_count: Failed requests
        timeout_count: Timeout requests
        error_rate: Error rate percentage
        availability: Availability percentage

        # Response Time Metrics
        response_time_avg: Average response time
        response_time_min: Minimum response time
        response_time_max: Maximum response time
        response_time_p50: 50th percentile
        response_time_p95: 95th percentile
        response_time_p99: 99th percentile

        # Timing Breakdown
        gateway_time_avg: Average gateway processing time
        backend_time_avg: Average backend service time

        # Throughput
        throughput: Requests per second

        # Data Transfer
        total_data_size: Total data transferred
        avg_request_size: Average request size
        avg_response_size: Average response size

        # Cache Metrics
        cache_hit_count: Cache hits
        cache_miss_count: Cache misses
        cache_bypass_count: Cache bypasses
        cache_hit_rate: Cache hit rate percentage

        # HTTP Status Codes
        status_2xx_count: 2xx responses
        status_3xx_count: 3xx responses
        status_4xx_count: 4xx responses
        status_5xx_count: 5xx responses
        status_codes: Detailed status code distribution

        # Per-Endpoint Breakdown (optional)
        endpoint_metrics: Per-endpoint metrics

        # Vendor-Specific Extensions
        vendor_metadata: Vendor-specific fields

        # Metadata
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    # ========================================================================
    # Core Identification
    # ========================================================================
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Gateway instance identifier")
    api_id: str = Field(..., description="API identifier")
    application_id: Optional[str] = Field(
        None, description="Application identifier (optional for app-level metrics)"
    )
    operation: Optional[str] = Field(
        None, description="Specific operation/endpoint (optional)"
    )

    # ========================================================================
    # Time Bucketing
    # ========================================================================
    timestamp: datetime = Field(..., description="Metric timestamp (start of time bucket)")
    time_bucket: TimeBucket = Field(..., description="Time bucket size")

    # ========================================================================
    # Request Counts
    # ========================================================================
    request_count: int = Field(..., ge=0, description="Total requests in bucket")
    success_count: int = Field(..., ge=0, description="Successful requests")
    failure_count: int = Field(..., ge=0, description="Failed requests")
    timeout_count: int = Field(default=0, ge=0, description="Timeout requests")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage (0-100)")
    availability: float = Field(..., ge=0, le=100, description="Availability percentage (0-100)")

    # ========================================================================
    # Response Time Metrics (milliseconds)
    # ========================================================================
    response_time_avg: float = Field(..., ge=0, description="Average response time (ms)")
    response_time_min: float = Field(..., ge=0, description="Minimum response time (ms)")
    response_time_max: float = Field(..., ge=0, description="Maximum response time (ms)")
    response_time_p50: float = Field(..., ge=0, description="50th percentile (ms)")
    response_time_p95: float = Field(..., ge=0, description="95th percentile (ms)")
    response_time_p99: float = Field(..., ge=0, description="99th percentile (ms)")

    # ========================================================================
    # Timing Breakdown
    # ========================================================================
    gateway_time_avg: float = Field(..., ge=0, description="Average gateway processing time (ms)")
    backend_time_avg: float = Field(..., ge=0, description="Average backend service time (ms)")

    # ========================================================================
    # Throughput
    # ========================================================================
    throughput: float = Field(..., ge=0, description="Requests per second")

    # ========================================================================
    # Data Transfer
    # ========================================================================
    total_data_size: int = Field(..., ge=0, description="Total data transferred (bytes)")
    avg_request_size: float = Field(..., ge=0, description="Average request size (bytes)")
    avg_response_size: float = Field(..., ge=0, description="Average response size (bytes)")

    # ========================================================================
    # Cache Metrics
    # ========================================================================
    cache_hit_count: int = Field(default=0, ge=0, description="Cache hits")
    cache_miss_count: int = Field(default=0, ge=0, description="Cache misses")
    cache_bypass_count: int = Field(default=0, ge=0, description="Cache bypasses")
    cache_hit_rate: float = Field(default=0, ge=0, le=100, description="Cache hit rate percentage")

    # ========================================================================
    # HTTP Status Codes
    # ========================================================================
    status_2xx_count: int = Field(default=0, ge=0, description="2xx responses")
    status_3xx_count: int = Field(default=0, ge=0, description="3xx responses")
    status_4xx_count: int = Field(default=0, ge=0, description="4xx responses")
    status_5xx_count: int = Field(default=0, ge=0, description="5xx responses")
    status_codes: dict[str, int] = Field(
        default_factory=dict, description="Detailed status code distribution (code: count)"
    )

    # ========================================================================
    # Per-Endpoint Breakdown (optional)
    # ========================================================================
    endpoint_metrics: Optional[list[EndpointMetric]] = Field(
        None, description="Per-endpoint metrics breakdown"
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
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # ========================================================================
    # Validators
    # ========================================================================

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
        """Validate p99 >= p95."""
        if "response_time_p95" in info.data and v < info.data["response_time_p95"]:
            raise ValueError("response_time_p99 must be >= response_time_p95")
        return v

    @field_validator("error_rate")
    @classmethod
    def validate_error_rate(cls, v: float, info) -> float:
        """Validate error_rate consistency with counts."""
        if "failure_count" in info.data and "request_count" in info.data:
            if info.data["request_count"] > 0:
                expected_rate = (info.data["failure_count"] / info.data["request_count"]) * 100
                if abs(v - expected_rate) > 0.1:  # Allow 0.1% tolerance
                    raise ValueError(
                        f"error_rate ({v}%) inconsistent with failure_count/request_count ({expected_rate}%)"
                    )
        return v

    @field_validator("cache_hit_rate")
    @classmethod
    def validate_cache_hit_rate(cls, v: float, info) -> float:
        """Validate cache_hit_rate consistency with counts."""
        if "cache_hit_count" in info.data and "cache_miss_count" in info.data:
            total_cache_requests = info.data["cache_hit_count"] + info.data["cache_miss_count"]
            if total_cache_requests > 0:
                expected_rate = (info.data["cache_hit_count"] / total_cache_requests) * 100
                if abs(v - expected_rate) > 0.1:  # Allow 0.1% tolerance
                    raise ValueError(
                        f"cache_hit_rate ({v}%) inconsistent with cache counts ({expected_rate}%)"
                    )
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate timestamp is within retention policy (90 days)."""
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        if v < ninety_days_ago:
            raise ValueError("timestamp must be within last 90 days (retention policy)")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440001",
                "api_id": "dfe828c7-ea69-4399-8807-83e07be8ebc6",
                "timestamp": "2026-03-09T15:00:00Z",
                "time_bucket": "5m",
                "request_count": 1500,
                "success_count": 1470,
                "failure_count": 30,
                "timeout_count": 0,
                "error_rate": 2.0,
                "availability": 98.0,
                "response_time_avg": 85.5,
                "response_time_min": 10.0,
                "response_time_max": 500.0,
                "response_time_p50": 75.0,
                "response_time_p95": 200.0,
                "response_time_p99": 350.0,
                "gateway_time_avg": 25.0,
                "backend_time_avg": 60.5,
                "throughput": 5.0,
                "total_data_size": 1500000,
                "avg_request_size": 500.0,
                "avg_response_size": 500.0,
                "cache_hit_count": 300,
                "cache_miss_count": 1200,
                "cache_bypass_count": 0,
                "cache_hit_rate": 20.0,
                "status_2xx_count": 1450,
                "status_3xx_count": 0,
                "status_4xx_count": 20,
                "status_5xx_count": 30,
                "status_codes": {"200": 1450, "404": 20, "500": 30},
                "endpoint_metrics": [
                    {
                        "endpoint": "/users/{id}",
                        "method": "GET",
                        "request_count": 800,
                        "success_count": 792,
                        "failure_count": 8,
                        "error_rate": 1.0,
                        "response_time_avg": 70.0,
                        "response_time_p50": 65.0,
                        "response_time_p95": 150.0,
                        "response_time_p99": 250.0,
                    }
                ],
            }
        }


# Made with Bob
