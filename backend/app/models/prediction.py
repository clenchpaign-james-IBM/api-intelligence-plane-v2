"""Prediction model for API Intelligence Plane.

Represents a failure prediction with target API, predicted failure time,
confidence score, contributing factors, and recommended actions.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PredictionType(str, Enum):
    """Type of API failure or issue being predicted.
    
    Categorizes predictions based on the nature of the anticipated problem,
    enabling targeted preventive actions and appropriate alerting.
    
    Attributes:
        FAILURE: Complete API failure or outage prediction - API will become unavailable
                or return errors for most/all requests.
        DEGRADATION: Performance degradation prediction - API will experience increased
                    latency, reduced throughput, or elevated error rates.
        CAPACITY: Capacity limit prediction - API will reach resource limits (rate limits,
                 connection pools, memory) causing request rejections.
        SECURITY: Security incident prediction - Potential security breach, attack pattern,
                 or vulnerability exploitation detected.
    """

    FAILURE = "failure"
    DEGRADATION = "degradation"
    CAPACITY = "capacity"
    SECURITY = "security"


class PredictionSeverity(str, Enum):
    """Predicted impact severity of the anticipated issue.
    
    Indicates the expected business and operational impact if the predicted
    event occurs, guiding prioritization of preventive actions.
    
    Attributes:
        CRITICAL: Severe impact - Complete service outage, data loss, or security breach
                 affecting multiple systems or users. Requires immediate action.
        HIGH: Significant impact - Major performance degradation or partial outage
             affecting substantial user base. Requires urgent attention.
        MEDIUM: Moderate impact - Noticeable performance issues or intermittent errors
               affecting some users. Should be addressed promptly.
        LOW: Minor impact - Slight performance degradation or isolated issues with
            minimal user impact. Can be addressed during normal operations.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PredictionStatus(str, Enum):
    """Current status of the prediction.
    
    Tracks the lifecycle of a prediction from creation through resolution,
    enabling accuracy measurement and model improvement.
    
    Attributes:
        ACTIVE: Prediction is active and the predicted event has not yet occurred
               or been prevented. Monitoring continues.
        RESOLVED: Predicted event was prevented through proactive intervention,
                 or the prediction window has passed without incident.
        FALSE_POSITIVE: Predicted event did not occur and was incorrectly predicted.
                       Used for model accuracy tracking and improvement.
        EXPIRED: Prediction window has passed without the event occurring and without
                preventive action. Different from false_positive as it may indicate
                natural resolution or insufficient data.
    """

    ACTIVE = "active"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    EXPIRED = "expired"


class ActualOutcome(str, Enum):
    """Actual outcome after the prediction window.
    
    Records what actually happened, enabling prediction accuracy measurement
    and machine learning model refinement.
    
    Attributes:
        OCCURRED: The predicted event actually occurred as anticipated. Validates
                 the prediction accuracy.
        PREVENTED: The predicted event was prevented through proactive intervention
                  based on the prediction. Demonstrates prediction value.
        FALSE_ALARM: The predicted event did not occur and was a false prediction.
                    Used for model accuracy tracking and tuning.
    """

    OCCURRED = "occurred"
    PREVENTED = "prevented"
    FALSE_ALARM = "false_alarm"


class ContributingFactorType(str, Enum):
    """Types of contributing factors for predictions."""
    
    # Performance Metrics
    INCREASING_ERROR_RATE = "increasing_error_rate"
    DEGRADING_RESPONSE_TIME = "degrading_response_time"
    GRADUAL_RESPONSE_TIME_INCREASE = "gradual_response_time_increase"
    HIGH_LATENCY_UNDER_LOAD = "high_latency_under_load"
    SPIKE_IN_5XX_ERRORS = "spike_in_5xx_errors"
    SPIKE_IN_4XX_ERRORS = "spike_in_4xx_errors"
    TIMEOUT_RATE_INCREASING = "timeout_rate_increasing"
    
    # Availability & Throughput
    DECLINING_AVAILABILITY = "declining_availability"
    DECLINING_THROUGHPUT = "declining_throughput"
    
    # Capacity
    RAPID_REQUEST_GROWTH = "rapid_request_growth"
    
    # Dependencies
    DOWNSTREAM_SERVICE_DEGRADATION = "downstream_service_degradation"
    
    # Traffic Patterns
    ABNORMAL_TRAFFIC_PATTERN = "abnormal_traffic_pattern"


class ContributingFactor(BaseModel):
    """Factor contributing to the prediction.
    
    Represents a specific metric or condition that contributes to the prediction,
    providing transparency into the prediction reasoning and enabling targeted
    remediation actions.
    
    Attributes:
        factor: Type of contributing factor from the ContributingFactorType enum.
        current_value: Current measured value of the metric (e.g., 0.15 for 15% error rate,
                      350.0 for 350ms response time).
        threshold: Threshold value that defines the acceptable limit for this metric.
                  Values exceeding this threshold contribute to the prediction.
        trend: Direction of change for this metric. Valid values: 'increasing',
              'decreasing', 'stable'. Indicates whether the situation is worsening.
        weight: Relative importance of this factor in the prediction (0.0 to 1.0).
               Higher weights indicate stronger contribution to the prediction.
               All weights across factors should sum to approximately 1.0.
    """

    factor: ContributingFactorType = Field(
        ...,
        description="Type of contributing factor from the ContributingFactorType enum."
    )
    current_value: float = Field(
        ...,
        description="Current measured value of the metric (e.g., 0.15 for 15% error rate, 350.0 for 350ms response time)."
    )
    threshold: float = Field(
        ...,
        description="Threshold value that defines the acceptable limit for this metric. Values exceeding this threshold contribute to the prediction."
    )
    trend: str = Field(
        ...,
        description="Direction of change for this metric. Valid values: 'increasing', 'decreasing', 'stable'. Indicates whether the situation is worsening."
    )
    weight: float = Field(
        ...,
        ge=0,
        le=1,
        description="Relative importance of this factor in the prediction (0.0 to 1.0). Higher weights indicate stronger contribution to the prediction. All weights across factors should sum to approximately 1.0."
    )


class Prediction(BaseModel):
    """Prediction entity representing a failure prediction.

    Attributes:
        id: Unique identifier (UUID v4)
        api_id: Target API
        prediction_type: Type of prediction
        predicted_at: When prediction made
        predicted_time: When event expected (24-48h from predicted_at)
        confidence_score: Confidence (0-1)
        severity: Impact severity
        status: Prediction status
        contributing_factors: Factors leading to prediction (at least 1)
        recommended_actions: Suggested remediation (at least 1)
        actual_outcome: What actually happened
        actual_time: When event occurred
        accuracy_score: Prediction accuracy (0-1, calculated post-event)
        model_version: ML model version
        metadata: Additional data
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Gateway where API is deployed")
    api_id: UUID = Field(..., description="Target API")
    api_name: Optional[str] = Field(None, description="API name (enriched from inventory)")
    prediction_type: PredictionType = Field(..., description="Type of prediction")
    predicted_at: datetime = Field(..., description="When prediction made")
    predicted_time: datetime = Field(..., description="When event expected")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence (0-1)")
    severity: PredictionSeverity = Field(..., description="Impact severity")
    status: PredictionStatus = Field(
        default=PredictionStatus.ACTIVE, description="Prediction status"
    )
    contributing_factors: list[ContributingFactor] = Field(
        ..., min_length=1, description="Factors leading to prediction"
    )
    recommended_actions: list[str] = Field(
        ..., min_length=1, description="Suggested remediation"
    )
    actual_outcome: Optional[ActualOutcome] = Field(
        None, description="What actually happened"
    )
    actual_time: Optional[datetime] = Field(None, description="When event occurred")
    accuracy_score: Optional[float] = Field(
        None, ge=0, le=1, description="Prediction accuracy (0-1)"
    )
    model_version: str = Field(..., description="ML model version")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("predicted_time")
    @classmethod
    def validate_predicted_time(cls, v: datetime, info) -> datetime:
        """Validate predicted_time is 24-48 hours after predicted_at."""
        if "predicted_at" in info.data:
            predicted_at = info.data["predicted_at"]
            min_time = predicted_at + timedelta(hours=24)
            max_time = predicted_at + timedelta(hours=48)
            if not (min_time <= v <= max_time):
                raise ValueError(
                    "predicted_time must be 24-48 hours after predicted_at"
                )
        return v

    @field_validator("contributing_factors")
    @classmethod
    def validate_contributing_factors(
        cls, v: list[ContributingFactor]
    ) -> list[ContributingFactor]:
        """Validate contributing_factors array is not empty."""
        if not v:
            raise ValueError("contributing_factors array cannot be empty")
        return v

    @field_validator("recommended_actions")
    @classmethod
    def validate_recommended_actions(cls, v: list[str]) -> list[str]:
        """Validate recommended_actions array is not empty."""
        if not v:
            raise ValueError("recommended_actions array cannot be empty")
        return v

    @field_validator("actual_time")
    @classmethod
    def validate_actual_time(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate if actual_outcome is set, actual_time must be set."""
        if "actual_outcome" in info.data and info.data["actual_outcome"] is not None:
            if v is None:
                raise ValueError("actual_time must be set when actual_outcome is set")
        return v

    @field_validator("accuracy_score")
    @classmethod
    def validate_accuracy_score(cls, v: Optional[float], info) -> Optional[float]:
        """Calculate accuracy_score as: 1 - |predicted_time - actual_time| / 48h."""
        if v is not None and "predicted_time" in info.data and "actual_time" in info.data:
            predicted_time = info.data["predicted_time"]
            actual_time = info.data["actual_time"]
            if actual_time:
                time_diff = abs((predicted_time - actual_time).total_seconds())
                hours_48 = 48 * 3600
                calculated_accuracy = 1 - (time_diff / hours_48)
                calculated_accuracy = max(0, min(1, calculated_accuracy))
                # Allow small floating point differences
                if abs(v - calculated_accuracy) > 0.01:
                    raise ValueError(
                        f"accuracy_score ({v}) should be approximately {calculated_accuracy}"
                    )
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "api_id": "550e8400-e29b-41d4-a716-446655440001",
                "prediction_type": "failure",
                "predicted_at": "2026-03-09T10:00:00Z",
                "predicted_time": "2026-03-10T18:00:00Z",
                "confidence_score": 0.85,
                "severity": "high",
                "status": "active",
                "contributing_factors": [
                    {
                        "factor": "increasing_error_rate",
                        "current_value": 0.15,
                        "threshold": 0.10,
                        "trend": "increasing",
                        "weight": 0.35,
                    },
                    {
                        "factor": "degrading_response_time",
                        "current_value": 350.0,
                        "threshold": 200.0,
                        "trend": "increasing",
                        "weight": 0.25,
                    },
                ],
                "recommended_actions": [
                    "Scale up API instances",
                    "Review recent code changes",
                    "Check database connection pool",
                ],
                "model_version": "1.2.0",
            }
        }

# Made with Bob
