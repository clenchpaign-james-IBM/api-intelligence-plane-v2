"""OptimizationRecommendation model for API Intelligence Plane.

Represents a performance optimization opportunity with target API,
recommendation type, estimated impact, implementation effort, and validation results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class AIContext(BaseModel):
    """AI-generated insights for optimization recommendations."""
    
    performance_analysis: Optional[str] = Field(
        default=None,
        description="AI-generated performance analysis"
    )
    
    implementation_guidance: Optional[str] = Field(
        default=None,
        description="AI-generated implementation guidance and best practices"
    )
    
    prioritization: Optional[str] = Field(
        default=None,
        description="AI-generated prioritization guidance"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When AI insights were generated"
    )

class OptimizationActionType(str, Enum):
    """Type of action taken on an optimization recommendation.
    
    Categorizes the remediation action for deterministic tracking and filtering.
    
    Attributes:
        APPLY_POLICY: Action to apply a policy to the gateway (caching, rate limiting).
        REMOVE_POLICY: Action to remove a previously applied policy from the gateway.
        VALIDATE: Action to validate the impact of an implemented recommendation.
        MANUAL_CONFIGURATION: Action requiring manual configuration (e.g., compression).
    """
    
    APPLY_POLICY = "apply_policy"
    REMOVE_POLICY = "remove_policy"
    VALIDATE = "validate"
    MANUAL_CONFIGURATION = "manual_configuration"


class OptimizationActionStatus(str, Enum):
    """Status of an optimization action.
    
    Tracks the current state of the action for workflow management.
    
    Attributes:
        COMPLETED: Action successfully completed.
        PENDING: Action is queued or awaiting execution.
        FAILED: Action failed to complete (see error_message for details).
        IN_PROGRESS: Action is currently being executed.
    """
    
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class OptimizationAction(BaseModel):
    """Action taken on an optimization recommendation.
    
    Records specific remediation actions for audit trail and debugging.
    Similar to RemediationAction in vulnerability model.
    
    Attributes:
        action: Description of the action taken (e.g., 'Applied caching policy',
               'Removed rate limit policy', 'Validation completed').
        type: Category of action (OptimizationActionType enum).
        status: Current status (OptimizationActionStatus enum).
        performed_at: UTC timestamp when the action was performed.
        performed_by: Identifier of who performed the action (user ID, 'system', 'automation').
        gateway_policy_id: ID of the gateway policy created/modified (if applicable).
        error_message: Error details if the action failed, for troubleshooting.
        metadata: Additional context about the action (configuration details, retry attempts, etc.).
    """
    
    action: str = Field(
        ...,
        description="Description of the action taken"
    )
    type: OptimizationActionType = Field(
        ...,
        description="Action type"
    )
    status: OptimizationActionStatus = Field(
        ...,
        description="Action status"
    )
    performed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When action was performed"
    )
    performed_by: str = Field(
        ...,
        description="Who performed the action (user ID, 'system', 'automation')"
    )
    gateway_policy_id: Optional[str] = Field(
        None,
        description="Gateway policy ID if applicable"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error details if failed"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Additional action context"
    )



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
    """Implementation priority level for optimization recommendations.
    
    Indicates the urgency and importance of implementing the recommendation
    based on potential impact and risk.
    
    Attributes:
        CRITICAL: Immediate action required - Severe performance issues or imminent
                 failures. Should be implemented within hours or days.
        HIGH: High priority - Significant performance impact or growing issues.
             Should be implemented within days or weeks.
        MEDIUM: Moderate priority - Noticeable improvements possible but not urgent.
               Should be implemented within weeks or months.
        LOW: Low priority - Minor optimizations or nice-to-have improvements.
            Can be implemented during normal maintenance cycles.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImplementationEffort(str, Enum):
    """Estimated effort required to implement the recommendation.
    
    Helps prioritize recommendations by balancing impact against implementation cost.
    
    Attributes:
        LOW: Minimal effort - Simple configuration changes or single-step implementations.
            Can typically be completed in hours. Examples: Enable compression, adjust cache TTL.
        MEDIUM: Moderate effort - Multiple configuration changes or minor code modifications.
               May require testing and coordination. Typically days to a week.
               Examples: Implement caching layer, configure rate limiting.
        HIGH: Significant effort - Major architectural changes, new infrastructure, or
             extensive code modifications. Requires planning, testing, and staged rollout.
             Typically weeks to months. Examples: Migrate to new architecture, major refactoring.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(str, Enum):
    """Current implementation status of the recommendation.
    
    Tracks the recommendation lifecycle from creation through implementation
    or rejection.
    
    Attributes:
        PENDING: Recommendation created but not yet acted upon. Awaiting review
                and implementation decision.
        IN_PROGRESS: Implementation has started but is not yet complete. May involve
                    multiple steps or staged rollout.
        IMPLEMENTED: Recommendation has been fully implemented and is active.
                    Validation results may be available.
        REJECTED: Recommendation was reviewed and rejected. May include reasons
                 in metadata (e.g., not feasible, conflicts with requirements).
        EXPIRED: Recommendation is no longer relevant due to time passage, system
                changes, or resolved conditions. Different from rejected.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EstimatedImpact(BaseModel):
    """Expected improvements from implementing recommendation.
    
    Quantifies the anticipated performance improvement to help prioritize
    recommendations and measure success after implementation.
    
    Attributes:
        metric: Name of the metric that will improve (e.g., 'response_time_p95',
               'error_rate', 'throughput', 'cpu_utilization').
        current_value: Current measured value of the metric before implementation.
                      Units depend on metric type (ms for latency, % for rates, etc.).
        expected_value: Predicted value of the metric after successful implementation.
                       Should be better than current_value.
        improvement_percentage: Expected improvement as a percentage (must be positive).
                              Calculated as: ((current - expected) / current) * 100.
        confidence: Confidence level in the estimate (0.0 to 1.0). Based on historical
                   data, similar implementations, and analysis certainty. Higher values
                   indicate more reliable predictions.
    """

    metric: str = Field(
        ...,
        description="Name of the metric that will improve (e.g., 'response_time_p95', 'error_rate', 'throughput', 'cpu_utilization')."
    )
    current_value: float = Field(
        ...,
        description="Current measured value of the metric before implementation. Units depend on metric type (ms for latency, % for rates, etc.)."
    )
    expected_value: float = Field(
        ...,
        description="Predicted value of the metric after successful implementation. Should be better than current_value."
    )
    improvement_percentage: float = Field(
        ...,
        gt=0,
        description="Expected improvement as a percentage (must be positive). Calculated as: ((current - expected) / current) * 100."
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence level in the estimate (0.0 to 1.0). Based on historical data, similar implementations, and analysis certainty. Higher values indicate more reliable predictions."
    )


class ActualImpact(BaseModel):
    """Actual impact measured after implementation.
    
    Records the real-world results of implementing the recommendation,
    enabling accuracy tracking and ROI calculation.
    
    Attributes:
        metric: Name of the metric that was measured (should match EstimatedImpact.metric).
        before_value: Measured value before implementation (baseline).
        after_value: Measured value after implementation (result).
        actual_improvement: Actual improvement percentage achieved.
                          Calculated as: ((before - after) / before) * 100.
                          Can be compared to estimated improvement for accuracy assessment.
    """

    metric: str = Field(
        ...,
        description="Name of the metric that was measured (should match EstimatedImpact.metric)."
    )
    before_value: float = Field(
        ...,
        description="Measured value before implementation (baseline)."
    )
    after_value: float = Field(
        ...,
        description="Measured value after implementation (result)."
    )
    actual_improvement: float = Field(
        ...,
        description="Actual improvement percentage achieved. Calculated as: ((before - after) / before) * 100. Can be compared to estimated improvement for accuracy assessment."
    )


class ValidationResults(BaseModel):
    """Post-implementation validation results.
    
    Captures the outcome of implementing a recommendation, including measured
    impact and success determination.
    
    Attributes:
        actual_impact: Measured performance impact after implementation.
        success: Whether the implementation achieved its goals. True if actual improvement
                meets or exceeds estimated improvement (within reasonable tolerance).
        measured_at: UTC timestamp when validation measurements were taken. Should be
                    after sufficient time for the change to take effect (typically hours
                    to days after implementation).
    """

    actual_impact: ActualImpact = Field(
        ...,
        description="Measured performance impact after implementation."
    )
    success: bool = Field(
        ...,
        description="Whether the implementation achieved its goals. True if actual improvement meets or exceeds estimated improvement (within reasonable tolerance)."
    )
    measured_at: datetime = Field(
        ...,
        description="UTC timestamp when validation measurements were taken. Should be after sufficient time for the change to take effect (typically hours to days after implementation)."
    )


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
        remediation_actions: History of actions taken on this recommendation
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
    remediation_actions: list[OptimizationAction] = Field(
        default_factory=list,
        description="History of actions taken on this recommendation"
    )
    cost_savings: Optional[float] = Field(
        None, ge=0, description="Estimated cost savings (USD per month)"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    vendor_metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Vendor-specific metadata (Gateway policy IDs, configurations, etc.)"
    )
    ai_context: Optional[AIContext] = Field(
        None,
        description="AI-generated insights and analysis"
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
    
    def to_llm_dict(self) -> dict[str, Any]:
        """
        Generate LLM-optimized dictionary representation.
        
        Trims large/redundant fields to reduce token count while maintaining
        essential context for natural language response generation.
        
        Estimated reduction: 50-70% for typical recommendation entities.
        
        Returns:
            Trimmed dictionary suitable for LLM context
        """
        result = {
            "id": str(self.id),
            "gateway_id": str(self.gateway_id),
            "api_id": str(self.api_id),
            "recommendation_type": self.recommendation_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "implementation_effort": self.implementation_effort.value,
            "status": self.status.value,
            "cost_savings": self.cost_savings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        # Trim estimated_impact - keep only key metrics
        result["estimated_impact"] = {
            "metric": self.estimated_impact.metric,
            "improvement_percentage": self.estimated_impact.improvement_percentage,
            "confidence": self.estimated_impact.confidence,
        }
        
        # Trim implementation_steps - keep first 3 only
        if self.implementation_steps:
            result["implementation_steps"] = self.implementation_steps[:3]
            if len(self.implementation_steps) > 3:
                result["implementation_steps_total"] = len(self.implementation_steps)
        
        # Trim validation_results - keep only success and actual_improvement
        if self.validation_results:
            result["validation_results"] = {
                "success": self.validation_results.success,
                "actual_improvement": self.validation_results.actual_impact.actual_improvement,
            }
        
        # Trim remediation_actions - keep count and latest action status
        if self.remediation_actions:
            result["remediation_actions_count"] = len(self.remediation_actions)
            latest = self.remediation_actions[-1]
            result["latest_action_status"] = latest.status.value
        
        # Trim ai_context - keep only performance_analysis (first 200 chars)
        if self.ai_context and self.ai_context.performance_analysis:
            result["ai_performance_analysis"] = self.ai_context.performance_analysis[:200]
        
        # Drop: vendor_metadata, metadata, full ai_context
        
        return result

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
