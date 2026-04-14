"""OptimizationRecommendation model for API Intelligence Plane.

Represents a performance optimization opportunity with target API,
recommendation type, estimated impact, implementation effort, and validation results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class RecommendationType(str, Enum):
    """Type of optimization.
    
    Only includes recommendations that can be validated with gateway-observable metrics.
    Removed: query_optimization, resource_allocation, connection_pooling
    (These require backend instrumentation to diagnose accurately)
    """

    CACHING = "caching"
    RATE_LIMITING = "rate_limiting"
    COMPRESSION = "compression"


class RecommendationPriority(str, Enum):
    """Implementation priority."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImplementationEffort(str, Enum):
    """Effort required."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(str, Enum):
    """Implementation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EstimatedImpact(BaseModel):
    """Expected improvements from implementing recommendation."""

    metric: str = Field(..., description="Metric to improve (e.g., 'response_time_p95')")
    current_value: float = Field(..., description="Current metric value")
    expected_value: float = Field(..., description="Expected metric value after implementation")
    improvement_percentage: float = Field(
        ..., gt=0, description="Expected improvement percentage"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence in estimate (0-1)")


class ActualImpact(BaseModel):
    """Actual impact measured after implementation."""

    metric: str = Field(..., description="Metric measured")
    before_value: float = Field(..., description="Value before implementation")
    after_value: float = Field(..., description="Value after implementation")
    actual_improvement: float = Field(..., description="Actual improvement percentage")


class ValidationResults(BaseModel):
    """Post-implementation validation results."""

    actual_impact: ActualImpact = Field(..., description="Measured impact")
    success: bool = Field(..., description="Whether implementation was successful")
    measured_at: datetime = Field(..., description="When results were measured")


class OptimizationRecommendation(BaseModel):
    """OptimizationRecommendation entity representing a performance optimization opportunity.

    Attributes:
        id: Unique identifier (UUID v4)
        api_id: Target API
        recommendation_type: Type of optimization
        title: Recommendation title (1-255 characters)
        description: Detailed description (1-5000 characters)
        priority: Implementation priority
        estimated_impact: Expected improvements
        implementation_effort: Effort required
        implementation_steps: How to implement (at least 1 step)
        status: Implementation status
        implemented_at: Implementation timestamp
        validation_results: Post-implementation metrics
        cost_savings: Estimated cost savings (USD per month)
        metadata: Additional data
        created_at: Creation timestamp
        updated_at: Last update timestamp
        expires_at: Recommendation expiry
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Gateway where API is deployed")
    api_id: UUID = Field(..., description="Target API")
    recommendation_type: RecommendationType = Field(..., description="Type of optimization")
    title: str = Field(
        ..., min_length=1, max_length=255, description="Recommendation title"
    )
    description: str = Field(
        ..., min_length=1, max_length=5000, description="Detailed description"
    )
    priority: RecommendationPriority = Field(..., description="Implementation priority")
    estimated_impact: EstimatedImpact = Field(..., description="Expected improvements")
    implementation_effort: ImplementationEffort = Field(..., description="Effort required")
    implementation_steps: list[str] = Field(
        ..., min_length=1, description="How to implement"
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING, description="Implementation status"
    )
    implemented_at: Optional[datetime] = Field(
        None, description="Implementation timestamp"
    )
    validation_results: Optional[ValidationResults] = Field(
        None, description="Post-implementation metrics"
    )
    cost_savings: Optional[float] = Field(
        None, ge=0, description="Estimated cost savings (USD per month)"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    vendor_metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Vendor-specific metadata (Gateway policy IDs, configurations, etc.)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiry")

    @field_validator("estimated_impact")
    @classmethod
    def validate_estimated_impact(cls, v: EstimatedImpact) -> EstimatedImpact:
        """Validate improvement_percentage is positive."""
        if v.improvement_percentage <= 0:
            raise ValueError("improvement_percentage must be positive")
        return v

    @field_validator("implementation_steps")
    @classmethod
    def validate_implementation_steps(cls, v: list[str]) -> list[str]:
        """Validate implementation_steps array is not empty."""
        if not v:
            raise ValueError("implementation_steps array cannot be empty")
        return v

    @field_validator("implemented_at")
    @classmethod
    def validate_implemented_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate if status is implemented, implemented_at must be set."""
        if "status" in info.data:
            status = info.data["status"]
            if status == RecommendationStatus.IMPLEMENTED and v is None:
                raise ValueError("implemented_at must be set when status is implemented")
        return v

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate expires_at > created_at."""
        if v is not None and "created_at" in info.data:
            created_at = info.data["created_at"]
            if v <= created_at:
                raise ValueError("expires_at must be > created_at")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "api_id": "550e8400-e29b-41d4-a716-446655440001",
                "recommendation_type": "caching",
                "title": "Implement Redis Caching for User Endpoints",
                "description": "Add Redis caching layer for frequently accessed user data endpoints to reduce database load and improve response times.",
                "priority": "high",
                "estimated_impact": {
                    "metric": "response_time_p95",
                    "current_value": 250.0,
                    "expected_value": 150.0,
                    "improvement_percentage": 40.0,
                    "confidence": 0.85,
                },
                "implementation_effort": "medium",
                "implementation_steps": [
                    "Set up Redis cluster",
                    "Implement caching middleware",
                    "Add cache invalidation logic",
                    "Test and monitor performance",
                ],
                "status": "pending",
                "cost_savings": 500.0,
            }
        }

# Made with Bob
