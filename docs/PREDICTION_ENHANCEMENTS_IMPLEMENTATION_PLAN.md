# Prediction Feature Enhancements - Implementation Plan

**Created**: 2026-04-13  
**Status**: Ready for Implementation  
**Priority**: Medium (Post-MVP Enhancements)

---

## Overview

This document provides detailed implementation plans for three key enhancements to the Prediction feature identified in the comprehensive analysis. These enhancements will improve prediction accuracy, reduce false positives, and enable continuous improvement through user feedback.

---

## Enhancement 1: Prediction Confidence Calibration

### Objective
Improve prediction confidence scores by calibrating them against historical accuracy data, adjusting scores based on past performance by factor type and API characteristics.

### Business Value
- More accurate confidence scores lead to better prioritization
- Reduces alert fatigue from over-confident false predictions
- Builds trust in the prediction system through demonstrated accuracy

### Implementation Steps

#### 1.1 Data Model Updates

**File**: `backend/app/models/prediction.py`

Add calibration metadata to Prediction model:

```python
class Prediction(BaseModel):
    # ... existing fields ...
    
    # New fields for calibration
    calibrated_confidence: Optional[float] = Field(
        None, ge=0, le=1, 
        description="Calibrated confidence score based on historical accuracy"
    )
    calibration_factor: Optional[float] = Field(
        None, 
        description="Factor applied to raw confidence (calibrated = raw * factor)"
    )
    raw_confidence: Optional[float] = Field(
        None, ge=0, le=1,
        description="Original uncalibrated confidence score"
    )
```

#### 1.2 Repository Methods

**File**: `backend/app/db/repositories/prediction_repository.py`

Add methods for accuracy tracking by factor type:

```python
def get_accuracy_by_factor_type(
    self,
    factor_type: ContributingFactorType,
    days: int = 90
) -> Dict[str, Any]:
    """
    Get historical accuracy statistics for a specific contributing factor type.
    
    Returns:
        Dict with average_accuracy, prediction_count, confidence_distribution
    """
    # Implementation: Query predictions with this factor type
    # Calculate average accuracy_score where actual_outcome is set
    # Group by confidence ranges (0-0.5, 0.5-0.7, 0.7-0.85, 0.85-1.0)
    pass

def get_accuracy_by_api_characteristics(
    self,
    api_id: Optional[str] = None,
    days: int = 90
) -> Dict[str, Any]:
    """
    Get accuracy statistics grouped by API characteristics.
    
    Returns:
        Dict with accuracy by API, prediction type, severity
    """
    pass
```

#### 1.3 Calibration Service

**File**: `backend/app/services/calibration_service.py` (NEW)

```python
"""
Prediction Calibration Service

Calibrates prediction confidence scores based on historical accuracy.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.models.prediction import (
    Prediction,
    ContributingFactor,
    ContributingFactorType,
)
from app.db.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)


class CalibrationService:
    """Service for calibrating prediction confidence scores."""
    
    # Minimum predictions needed for calibration
    MIN_PREDICTIONS_FOR_CALIBRATION = 20
    
    # Calibration update frequency (days)
    CALIBRATION_UPDATE_DAYS = 7
    
    def __init__(self, prediction_repository: PredictionRepository):
        self.prediction_repo = prediction_repository
        self._calibration_factors = {}  # Cache calibration factors
        self._last_update = None
    
    def calibrate_confidence(
        self,
        raw_confidence: float,
        contributing_factors: List[ContributingFactor],
        api_id: str,
    ) -> Dict[str, float]:
        """
        Calibrate confidence score based on historical accuracy.
        
        Args:
            raw_confidence: Original confidence score (0-1)
            contributing_factors: List of contributing factors
            api_id: API identifier
            
        Returns:
            Dict with calibrated_confidence and calibration_factor
        """
        # Update calibration factors if needed
        self._update_calibration_factors_if_needed()
        
        # Calculate calibration factor based on:
        # 1. Factor type accuracy
        # 2. API-specific accuracy
        # 3. Confidence range accuracy
        
        factor_calibrations = []
        for factor in contributing_factors:
            factor_stats = self._get_factor_calibration(factor.factor)
            if factor_stats:
                factor_calibrations.append(factor_stats['calibration_factor'])
        
        # Weighted average of calibration factors
        if factor_calibrations:
            avg_calibration = sum(factor_calibrations) / len(factor_calibrations)
        else:
            avg_calibration = 1.0  # No calibration data, use raw confidence
        
        # Apply calibration
        calibrated = raw_confidence * avg_calibration
        calibrated = max(0.0, min(1.0, calibrated))  # Clamp to [0, 1]
        
        return {
            'calibrated_confidence': calibrated,
            'calibration_factor': avg_calibration,
        }
    
    def _update_calibration_factors_if_needed(self):
        """Update calibration factors if cache is stale."""
        if (self._last_update is None or 
            datetime.utcnow() - self._last_update > timedelta(days=self.CALIBRATION_UPDATE_DAYS)):
            self._update_calibration_factors()
    
    def _update_calibration_factors(self):
        """Recalculate calibration factors from historical data."""
        logger.info("Updating prediction calibration factors")
        
        # For each factor type, calculate average accuracy
        for factor_type in ContributingFactorType:
            stats = self.prediction_repo.get_accuracy_by_factor_type(
                factor_type=factor_type,
                days=90
            )
            
            if stats['prediction_count'] >= self.MIN_PREDICTIONS_FOR_CALIBRATION:
                # Calculate calibration factor
                # If average accuracy is 0.7 but average confidence was 0.9,
                # calibration factor = 0.7 / 0.9 = 0.78
                avg_accuracy = stats['average_accuracy']
                avg_confidence = stats['average_confidence']
                
                if avg_confidence > 0:
                    calibration_factor = avg_accuracy / avg_confidence
                else:
                    calibration_factor = 1.0
                
                self._calibration_factors[factor_type] = {
                    'calibration_factor': calibration_factor,
                    'sample_size': stats['prediction_count'],
                    'average_accuracy': avg_accuracy,
                }
        
        self._last_update = datetime.utcnow()
        logger.info(f"Updated calibration factors for {len(self._calibration_factors)} factor types")
    
    def _get_factor_calibration(self, factor_type: ContributingFactorType) -> Optional[Dict]:
        """Get calibration data for a specific factor type."""
        return self._calibration_factors.get(factor_type)
```

#### 1.4 Integration with Prediction Service

**File**: `backend/app/services/prediction_service.py`

Update prediction generation to use calibration:

```python
from app.services.calibration_service import CalibrationService

class PredictionService:
    def __init__(
        self,
        prediction_repository: PredictionRepository,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
        llm_service: Optional[Any] = None,
    ):
        # ... existing initialization ...
        self.calibration_service = CalibrationService(prediction_repository)
    
    def _create_prediction(
        self,
        api_id: UUID,
        prediction_type: PredictionType,
        raw_confidence: float,
        contributing_factors: List[ContributingFactor],
        # ... other params ...
    ) -> Prediction:
        """Create prediction with calibrated confidence."""
        
        # Calibrate confidence
        calibration_result = self.calibration_service.calibrate_confidence(
            raw_confidence=raw_confidence,
            contributing_factors=contributing_factors,
            api_id=str(api_id),
        )
        
        # Create prediction with both raw and calibrated confidence
        prediction = Prediction(
            api_id=api_id,
            prediction_type=prediction_type,
            confidence_score=calibration_result['calibrated_confidence'],
            raw_confidence=raw_confidence,
            calibrated_confidence=calibration_result['calibrated_confidence'],
            calibration_factor=calibration_result['calibration_factor'],
            contributing_factors=contributing_factors,
            # ... other fields ...
        )
        
        return prediction
```

#### 1.5 API Endpoints

**File**: `backend/app/api/v1/predictions.py`

Add endpoint for calibration statistics:

```python
@router.get(
    "/predictions/calibration/stats",
    summary="Get calibration statistics",
)
async def get_calibration_stats() -> dict:
    """
    Get prediction calibration statistics.
    
    Returns calibration factors and accuracy by factor type.
    """
    prediction_repo = PredictionRepository()
    calibration_service = CalibrationService(prediction_repo)
    
    # Force update to get latest stats
    calibration_service._update_calibration_factors()
    
    return {
        "status": "success",
        "calibration_factors": calibration_service._calibration_factors,
        "last_updated": calibration_service._last_update.isoformat(),
    }
```

### Testing Strategy

1. **Unit Tests**: Test calibration calculations with known accuracy data
2. **Integration Tests**: Verify calibration is applied during prediction generation
3. **E2E Tests**: Validate calibrated predictions are stored and retrieved correctly

### Success Metrics

- Calibrated confidence scores correlate better with actual outcomes (R² > 0.8)
- Reduction in over-confident false predictions by 30%
- User trust scores improve (measured through feedback)

---

## Enhancement 3: Seasonal Pattern Detection

### Objective
Implement seasonal decomposition to distinguish between expected traffic variations and true anomalies, reducing false positives during known high-traffic periods.

### Business Value
- Reduces alert fatigue from expected seasonal variations
- Improves prediction accuracy by 15-20%
- Better resource planning around seasonal events

### Implementation Steps

#### 3.1 Data Model Updates

**File**: `backend/app/models/base/metric.py`

Add seasonal metadata:

```python
class Metric(BaseModel):
    # ... existing fields ...
    
    # Seasonal analysis fields
    seasonal_component: Optional[float] = Field(
        None,
        description="Seasonal component from decomposition"
    )
    trend_component: Optional[float] = Field(
        None,
        description="Trend component from decomposition"
    )
    residual_component: Optional[float] = Field(
        None,
        description="Residual component (actual - seasonal - trend)"
    )
    is_seasonal_anomaly: Optional[bool] = Field(
        None,
        description="Whether this metric represents a seasonal anomaly"
    )
```

#### 3.2 Seasonal Analysis Service

**File**: `backend/app/services/seasonal_analysis_service.py` (NEW)

```python
"""
Seasonal Analysis Service

Performs seasonal decomposition and anomaly detection on time-series metrics.
Uses STL (Seasonal and Trend decomposition using Loess) algorithm.
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import signal
from statsmodels.tsa.seasonal import STL

from app.models.base.metric import Metric

logger = logging.getLogger(__name__)


class SeasonalAnalysisService:
    """Service for seasonal pattern detection and anomaly identification."""
    
    # Minimum data points for seasonal analysis
    MIN_DATA_POINTS = 168  # 1 week of hourly data
    
    # Seasonal periods (in hours)
    DAILY_PERIOD = 24
    WEEKLY_PERIOD = 168
    
    # Anomaly detection threshold (number of standard deviations)
    ANOMALY_THRESHOLD = 3.0
    
    def __init__(self):
        self._seasonal_models = {}  # Cache seasonal models by API
    
    def decompose_time_series(
        self,
        metrics: List[Metric],
        period: int = DAILY_PERIOD,
    ) -> Dict[str, List[float]]:
        """
        Perform seasonal decomposition on metric time series.
        
        Args:
            metrics: List of metrics in chronological order
            period: Seasonal period (default: 24 hours)
            
        Returns:
            Dict with trend, seasonal, and residual components
        """
        if len(metrics) < self.MIN_DATA_POINTS:
            logger.warning(f"Insufficient data for seasonal decomposition: {len(metrics)} points")
            return {
                'trend': [],
                'seasonal': [],
                'residual': [],
            }
        
        # Extract time series values (e.g., response times)
        values = np.array([m.response_time_avg for m in metrics])
        
        # Perform STL decomposition
        try:
            stl = STL(values, period=period, seasonal=13)
            result = stl.fit()
            
            return {
                'trend': result.trend.tolist(),
                'seasonal': result.seasonal.tolist(),
                'residual': result.resid.tolist(),
            }
        except Exception as e:
            logger.error(f"Seasonal decomposition failed: {e}")
            return {
                'trend': [],
                'seasonal': [],
                'residual': [],
            }
    
    def detect_seasonal_anomalies(
        self,
        metrics: List[Metric],
        decomposition: Dict[str, List[float]],
    ) -> List[Tuple[int, float]]:
        """
        Detect anomalies in the residual component.
        
        Args:
            metrics: Original metrics
            decomposition: Decomposition results
            
        Returns:
            List of (index, anomaly_score) tuples
        """
        residuals = decomposition['residual']
        if not residuals:
            return []
        
        # Calculate statistics on residuals
        residuals_array = np.array(residuals)
        mean = np.mean(residuals_array)
        std = np.std(residuals_array)
        
        # Detect anomalies (values beyond threshold standard deviations)
        anomalies = []
        for i, residual in enumerate(residuals):
            z_score = abs((residual - mean) / std) if std > 0 else 0
            if z_score > self.ANOMALY_THRESHOLD:
                anomalies.append((i, z_score))
        
        return anomalies
    
    def is_expected_variation(
        self,
        current_value: float,
        historical_metrics: List[Metric],
        tolerance: float = 2.0,
    ) -> bool:
        """
        Determine if current value is within expected seasonal variation.
        
        Args:
            current_value: Current metric value
            historical_metrics: Historical metrics for comparison
            tolerance: Number of standard deviations for tolerance
            
        Returns:
            True if within expected variation, False if anomalous
        """
        if len(historical_metrics) < self.MIN_DATA_POINTS:
            return True  # Not enough data, assume expected
        
        # Decompose historical data
        decomposition = self.decompose_time_series(historical_metrics)
        
        if not decomposition['residual']:
            return True  # Decomposition failed, assume expected
        
        # Get expected value (trend + seasonal at current time)
        # For simplicity, use last known trend + seasonal pattern
        expected_trend = decomposition['trend'][-1]
        
        # Get seasonal component for current hour of day/week
        current_hour = datetime.utcnow().hour
        seasonal_pattern = decomposition['seasonal']
        seasonal_value = seasonal_pattern[current_hour % len(seasonal_pattern)]
        
        expected_value = expected_trend + seasonal_value
        
        # Calculate residual
        residual = current_value - expected_value
        
        # Check if residual is within tolerance
        residuals_array = np.array(decomposition['residual'])
        std = np.std(residuals_array)
        
        return abs(residual) <= (tolerance * std)
    
    def get_seasonal_forecast(
        self,
        historical_metrics: List[Metric],
        hours_ahead: int = 48,
    ) -> List[Dict[str, float]]:
        """
        Forecast expected values based on seasonal patterns.
        
        Args:
            historical_metrics: Historical metrics
            hours_ahead: Number of hours to forecast
            
        Returns:
            List of forecasted values with confidence intervals
        """
        decomposition = self.decompose_time_series(historical_metrics)
        
        if not decomposition['trend']:
            return []
        
        # Simple forecast: extend trend + repeat seasonal pattern
        last_trend = decomposition['trend'][-1]
        seasonal_pattern = decomposition['seasonal']
        
        forecasts = []
        for h in range(hours_ahead):
            seasonal_index = (len(seasonal_pattern) + h) % len(seasonal_pattern)
            seasonal_value = seasonal_pattern[seasonal_index]
            
            forecast_value = last_trend + seasonal_value
            
            forecasts.append({
                'hours_ahead': h + 1,
                'forecast_value': forecast_value,
                'trend': last_trend,
                'seasonal': seasonal_value,
            })
        
        return forecasts
```

#### 3.3 Integration with Prediction Service

**File**: `backend/app/services/prediction_service.py`

Update to use seasonal analysis:

```python
from app.services.seasonal_analysis_service import SeasonalAnalysisService

class PredictionService:
    def __init__(self, ...):
        # ... existing initialization ...
        self.seasonal_service = SeasonalAnalysisService()
    
    def _analyze_failure_risk(
        self, api_id: UUID, metrics: List[Metric]
    ) -> Optional[Prediction]:
        """Analyze metrics for failure risk with seasonal awareness."""
        
        # Perform seasonal decomposition
        decomposition = self.seasonal_service.decompose_time_series(metrics)
        
        # Detect seasonal anomalies
        anomalies = self.seasonal_service.detect_seasonal_anomalies(
            metrics, decomposition
        )
        
        # Only generate prediction if anomalies are detected
        # (not just seasonal variations)
        if not anomalies:
            logger.info(f"No seasonal anomalies detected for API {api_id}")
            return None
        
        # Continue with existing prediction logic...
        # But adjust confidence based on seasonal context
        contributing_factors = []
        
        # Check if current error rate is expected variation
        current_error_rate = metrics[-1].error_rate
        is_expected = self.seasonal_service.is_expected_variation(
            current_value=current_error_rate,
            historical_metrics=metrics[:-1],  # Exclude current
        )
        
        if is_expected:
            logger.info(f"Error rate within expected seasonal variation for API {api_id}")
            return None  # Don't generate prediction for expected variations
        
        # ... rest of prediction logic ...
```

### Testing Strategy

1. **Unit Tests**: Test seasonal decomposition with synthetic data
2. **Integration Tests**: Verify seasonal patterns are detected correctly
3. **E2E Tests**: Validate predictions account for seasonal variations

### Success Metrics

- 30% reduction in false positive predictions during known seasonal events
- Improved prediction precision (fewer false alarms)
- User satisfaction with prediction relevance

---

## Enhancement 4: Prediction Feedback Loop

### Objective
Enable users to provide feedback on prediction helpfulness and accuracy, using this data to continuously improve prediction algorithms.

### Business Value
- Continuous improvement through user feedback
- Better understanding of prediction value
- Prioritization of algorithm improvements based on user needs

### Implementation Steps

#### 4.1 Data Model Updates

**File**: `backend/app/models/prediction.py`

Add feedback model:

```python
class PredictionFeedbackType(str, Enum):
    """Type of feedback."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    FALSE_POSITIVE = "false_positive"
    MISSED_ISSUE = "missed_issue"


class PredictionFeedback(BaseModel):
    """User feedback on prediction."""
    
    id: UUID = Field(default_factory=uuid4)
    prediction_id: UUID = Field(..., description="Related prediction")
    feedback_type: PredictionFeedbackType = Field(..., description="Feedback type")
    user_id: Optional[str] = Field(None, description="User who provided feedback")
    comment: Optional[str] = Field(None, description="Optional comment")
    action_taken: Optional[str] = Field(None, description="Action taken in response")
    was_prevented: Optional[bool] = Field(None, description="Was issue prevented")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Update Prediction model:

```python
class Prediction(BaseModel):
    # ... existing fields ...
    
    # Feedback fields
    feedback_count: int = Field(default=0, description="Number of feedback items")
    helpful_count: int = Field(default=0, description="Number of helpful votes")
    not_helpful_count: int = Field(default=0, description="Number of not helpful votes")
    feedback_score: Optional[float] = Field(
        None, ge=0, le=1,
        description="Feedback score (helpful / total)"
    )
```

#### 4.2 Repository Methods

**File**: `backend/app/db/repositories/prediction_repository.py`

Add feedback methods:

```python
def add_feedback(
    self,
    prediction_id: str,
    feedback: PredictionFeedback,
) -> bool:
    """
    Add feedback to a prediction.
    
    Args:
        prediction_id: Prediction UUID
        feedback: Feedback object
        
    Returns:
        True if successful
    """
    # Store feedback in separate index
    # Update prediction feedback counts
    pass

def get_feedback_for_prediction(
    self,
    prediction_id: str,
) -> List[PredictionFeedback]:
    """Get all feedback for a prediction."""
    pass

def get_feedback_statistics(
    self,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get feedback statistics.
    
    Returns:
        Dict with feedback counts, scores, trends
    """
    pass
```

#### 4.3 API Endpoints

**File**: `backend/app/api/v1/predictions.py`

Add feedback endpoints:

```python
@router.post(
    "/predictions/{prediction_id}/feedback",
    status_code=http_status.HTTP_201_CREATED,
    summary="Submit prediction feedback",
)
async def submit_feedback(
    prediction_id: UUID,
    feedback_type: PredictionFeedbackType,
    comment: Optional[str] = None,
    action_taken: Optional[str] = None,
    was_prevented: Optional[bool] = None,
) -> dict:
    """
    Submit feedback on a prediction.
    
    Args:
        prediction_id: Prediction UUID
        feedback_type: Type of feedback
        comment: Optional comment
        action_taken: Action taken in response
        was_prevented: Whether issue was prevented
        
    Returns:
        Feedback confirmation
    """
    prediction_repo = PredictionRepository()
    
    # Create feedback
    feedback = PredictionFeedback(
        prediction_id=prediction_id,
        feedback_type=feedback_type,
        comment=comment,
        action_taken=action_taken,
        was_prevented=was_prevented,
    )
    
    # Store feedback
    success = prediction_repo.add_feedback(str(prediction_id), feedback)
    
    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback",
        )
    
    return {
        "status": "success",
        "message": "Feedback submitted successfully",
        "feedback_id": str(feedback.id),
    }


@router.get(
    "/predictions/{prediction_id}/feedback",
    summary="Get prediction feedback",
)
async def get_feedback(
    prediction_id: UUID,
) -> dict:
    """Get all feedback for a prediction."""
    prediction_repo = PredictionRepository()
    
    feedback_list = prediction_repo.get_feedback_for_prediction(str(prediction_id))
    
    return {
        "status": "success",
        "prediction_id": str(prediction_id),
        "feedback": [
            {
                "id": str(f.id),
                "feedback_type": f.feedback_type.value,
                "comment": f.comment,
                "action_taken": f.action_taken,
                "was_prevented": f.was_prevented,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedback_list
        ],
    }


@router.get(
    "/predictions/feedback/stats",
    summary="Get feedback statistics",
)
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=90),
) -> dict:
    """Get prediction feedback statistics."""
    prediction_repo = PredictionRepository()
    
    stats = prediction_repo.get_feedback_statistics(days=days)
    
    return {
        "status": "success",
        "period_days": days,
        "statistics": stats,
    }
```

#### 4.4 Frontend Components

**File**: `frontend/src/components/predictions/PredictionFeedback.tsx` (NEW)

```typescript
import { ThumbsUp, ThumbsDown, MessageSquare } from 'lucide-react';
import { useState } from 'react';
import { api } from '../../services/api';

interface PredictionFeedbackProps {
  predictionId: string;
  onFeedbackSubmitted?: () => void;
}

const PredictionFeedback = ({ predictionId, onFeedbackSubmitted }: PredictionFeedbackProps) => {
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [actionTaken, setActionTaken] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleFeedback = async (feedbackType: 'helpful' | 'not_helpful') => {
    setSubmitting(true);
    try {
      await api.predictions.submitFeedback(predictionId, {
        feedback_type: feedbackType,
        comment: comment || undefined,
        action_taken: actionTaken || undefined,
      });
      
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
      
      // Reset form
      setComment('');
      setActionTaken('');
      setShowComment(false);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="border-t border-gray-200 pt-4 mt-4">
      <p className="text-sm text-gray-600 mb-2">Was this prediction helpful?</p>
      
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleFeedback('helpful')}
          disabled={submitting}
          className="flex items-center gap-1 px-3 py-1 rounded bg-green-100 hover:bg-green-200 text-green-700 transition-colors disabled:opacity-50"
        >
          <ThumbsUp className="w-4 h-4" />
          Helpful
        </button>
        
        <button
          onClick={() => handleFeedback('not_helpful')}
          disabled={submitting}
          className="flex items-center gap-1 px-3 py-1 rounded bg-red-100 hover:bg-red-200 text-red-700 transition-colors disabled:opacity-50"
        >
          <ThumbsDown className="w-4 h-4" />
          Not Helpful
        </button>
        
        <button
          onClick={() => setShowComment(!showComment)}
          className="flex items-center gap-1 px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          Add Comment
        </button>
      </div>
      
      {showComment && (
        <div className="mt-3 space-y-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell us more about this prediction..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />
          
          <input
            type="text"
            value={actionTaken}
            onChange={(e) => setActionTaken(e.target.value)}
            placeholder="What action did you take? (optional)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}
    </div>
  );
};

export default PredictionFeedback;
```

Update `PredictionCard.tsx` to include feedback component:

```typescript
import PredictionFeedback from './PredictionFeedback';

// In PredictionCard component, add at the end:
{detailed && prediction.status === 'active' && (
  <PredictionFeedback 
    predictionId={prediction.id}
    onFeedbackSubmitted={() => {
      // Optionally refetch prediction to update feedback counts
    }}
  />
)}
```

### Testing Strategy

1. **Unit Tests**: Test feedback submission and aggregation
2. **Integration Tests**: Verify feedback updates prediction statistics
3. **E2E Tests**: Validate complete feedback workflow from UI to storage

### Success Metrics

- 40% of predictions receive user feedback within 48 hours
- Feedback score correlates with prediction accuracy (R² > 0.7)
- Algorithm improvements based on feedback reduce not-helpful votes by 25%

---

## Implementation Priority

1. **Phase 1** (Weeks 1-2): Enhancement 4 - Prediction Feedback Loop
   - Quickest to implement
   - Provides immediate user value
   - Generates data for other enhancements

2. **Phase 2** (Weeks 3-5): Enhancement 1 - Confidence Calibration
   - Requires feedback data from Phase 1
   - Moderate complexity
   - High impact on prediction quality

3. **Phase 3** (Weeks 6-8): Enhancement 3 - Seasonal Pattern Detection
   - Most complex implementation
   - Requires statistical libraries
   - Highest technical value

---

## Dependencies

### Python Packages
```
statsmodels>=0.14.0  # For STL decomposition
scipy>=1.11.0        # For signal processing
numpy>=1.24.0        # For numerical operations
```

### Database Indices
- `prediction-feedback` index for feedback storage
- Additional fields in `api-predictions` index for calibration metadata

---

## Rollout Strategy

1. **Beta Testing**: Deploy to 10% of users for 2 weeks
2. **Monitoring**: Track prediction accuracy, feedback rates, false positive reduction
3. **Gradual Rollout**: Increase to 50%, then 100% based on metrics
4. **Feedback Loop**: Iterate based on user feedback and performance data

---

## Success Criteria

### Overall Goals
- 20% improvement in prediction accuracy
- 30% reduction in false positives
- 40% user feedback participation rate
- 90% user satisfaction with prediction relevance

### Technical Metrics
- Calibration R² > 0.8
- Seasonal anomaly detection precision > 85%
- Feedback processing latency < 100ms
- No performance degradation in prediction generation

---

**Document Status**: Ready for Review and Implementation  
**Next Steps**: Review with team, prioritize phases, allocate resources