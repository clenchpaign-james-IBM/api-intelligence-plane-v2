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
    """Type of prediction."""

    FAILURE = "failure"
    DEGRADATION = "degradation"
    CAPACITY = "capacity"
    SECURITY = "security"


class PredictionSeverity(str, Enum):
    """Impact severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PredictionStatus(str, Enum):
    """Prediction status."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    EXPIRED = "expired"


class ActualOutcome(str, Enum):
    """What actually happened."""

    OCCURRED = "occurred"
    PREVENTED = "prevented"
    FALSE_ALARM = "false_alarm"


class ContributingFactor(BaseModel):
    """Factor leading to prediction."""

    factor: str = Field(..., description="Factor name (e.g., 'increasing_error_rate')")
    current_value: float = Field(..., description="Current value")
    threshold: float = Field(..., description="Threshold value")
    trend: str = Field(..., description="Trend direction (increasing, decreasing, stable)")
    weight: float = Field(..., ge=0, le=1, description="Factor weight (0-1)")


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
    api_id: UUID = Field(..., description="Target API")
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
