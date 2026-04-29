"""
Integration tests for prediction accuracy tracking.

Tests the prediction accuracy tracking workflow:
1. Create predictions
2. Simulate actual outcomes
3. Track accuracy scores
4. Verify accuracy calculations
5. Test accuracy reporting
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.app.db.repositories.prediction_repository import PredictionRepository
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.services.prediction_service import PredictionService
from backend.app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
    ActualOutcome,
    ContributingFactor,
    ContributingFactorType,
)
from backend.app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    IntelligenceMetadata,
)


@pytest.fixture
async def opensearch_client():
    """Get OpenSearch client for tests."""
    client = get_opensearch_client()
    yield client


@pytest.fixture
async def prediction_repository(opensearch_client):
    """Create Prediction repository instance."""
    return PredictionRepository()


@pytest.fixture
async def api_repository(opensearch_client):
    """Create API repository instance."""
    return APIRepository()


@pytest.fixture
async def test_api(api_repository):
    """Create a test API for accuracy tracking."""
    gateway_id = uuid4()
    api_id = uuid4()
    now = datetime.utcnow()
    
    # Create minimal API for testing
    api_data = {
        "id": str(api_id),
        "gateway_id": str(gateway_id),
        "name": "Accuracy Test API",
        "base_path": "/api/v1/test",
        "endpoints": [{"path": "/test", "method": "GET"}],
        "methods": ["GET"],
        "authentication_type": "none",
        "intelligence_metadata": {
            "is_shadow": False,
            "discovery_method": "registered",
            "discovered_at": now.isoformat(),
            "last_seen_at": now.isoformat(),
            "health_score": 85.0,
        },
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    created_api = await api_repository.create_from_dict(api_data)
    yield created_api, gateway_id
    
    # Cleanup
    try:
        await api_repository.delete(str(api_id))
    except Exception:
        pass


@pytest.fixture
async def test_prediction(prediction_repository, test_api):
    """Create a test prediction for accuracy tracking."""
    api, gateway_id = test_api
    now = datetime.utcnow()
    
    prediction = Prediction(
        id=uuid4(),
        gateway_id=gateway_id,
        api_id=api.id,
        api_name=api.name,
        prediction_type=PredictionType.FAILURE,
        predicted_at=now,
        predicted_time=now + timedelta(hours=48),
        confidence_score=0.85,
        severity=PredictionSeverity.HIGH,
        status=PredictionStatus.ACTIVE,
        contributing_factors=[
            ContributingFactor(
                factor=ContributingFactorType.INCREASING_ERROR_RATE,
                current_value=15.0,
                threshold=10.0,
                trend="increasing",
                weight=0.4,
            )
        ],
        recommended_actions=["Investigate error logs", "Scale resources"],
        actual_outcome=None,
        actual_time=None,
        accuracy_score=None,
        model_version="1.0.0",
        metadata={},
    )
    
    created_prediction = await prediction_repository.create(prediction)
    yield created_prediction
    
    # Cleanup
    try:
        await prediction_repository.delete(str(created_prediction.id))
    except Exception:
        pass


@pytest.mark.asyncio
class TestPredictionAccuracy:
    """Integration tests for prediction accuracy tracking."""

    async def test_track_occurred_outcome(
        self, prediction_repository, test_prediction
    ):
        """Test tracking when predicted event actually occurred."""
        # Simulate event occurrence
        actual_time = datetime.utcnow()
        
        # Update prediction with actual outcome
        test_prediction.actual_outcome = ActualOutcome.OCCURRED
        test_prediction.actual_time = actual_time
        test_prediction.status = PredictionStatus.RESOLVED
        
        # Calculate accuracy score (time-based)
        time_diff = abs((actual_time - test_prediction.predicted_time).total_seconds())
        max_diff = 48 * 3600  # 48 hours in seconds
        accuracy = max(0.0, 1.0 - (time_diff / max_diff))
        test_prediction.accuracy_score = accuracy
        
        # Update in repository
        updated = await prediction_repository.update(test_prediction)
        
        # Verify accuracy tracking
        assert updated.actual_outcome == ActualOutcome.OCCURRED
        assert updated.actual_time is not None
        assert updated.accuracy_score is not None
        assert 0.0 <= updated.accuracy_score <= 1.0
        assert updated.status == PredictionStatus.RESOLVED

    async def test_track_prevented_outcome(
        self, prediction_repository, test_prediction
    ):
        """Test tracking when predicted event was prevented."""
        # Simulate preventive action
        actual_time = datetime.utcnow()
        
        # Update prediction with prevented outcome
        test_prediction.actual_outcome = ActualOutcome.PREVENTED
        test_prediction.actual_time = actual_time
        test_prediction.status = PredictionStatus.RESOLVED
        # Prevented outcomes get high accuracy if action was taken before predicted time
        test_prediction.accuracy_score = 0.95
        
        # Update in repository
        updated = await prediction_repository.update(test_prediction)
        
        # Verify tracking
        assert updated.actual_outcome == ActualOutcome.PREVENTED
        assert updated.accuracy_score == 0.95
        assert updated.status == PredictionStatus.RESOLVED

    async def test_track_false_alarm_outcome(
        self, prediction_repository, test_prediction
    ):
        """Test tracking when prediction was a false alarm."""
        # Simulate false alarm (event didn't occur)
        actual_time = test_prediction.predicted_time + timedelta(hours=24)
        
        # Update prediction with false alarm outcome
        test_prediction.actual_outcome = ActualOutcome.FALSE_ALARM
        test_prediction.actual_time = actual_time
        test_prediction.status = PredictionStatus.FALSE_POSITIVE
        # False alarms get 0 accuracy
        test_prediction.accuracy_score = 0.0
        
        # Update in repository
        updated = await prediction_repository.update(test_prediction)
        
        # Verify tracking
        assert updated.actual_outcome == ActualOutcome.FALSE_ALARM
        assert updated.accuracy_score == 0.0
        assert updated.status == PredictionStatus.FALSE_POSITIVE

    async def test_accuracy_score_calculation(
        self, prediction_repository, test_prediction
    ):
        """Test accuracy score calculation based on time difference."""
        # Test perfect prediction (occurred exactly at predicted time)
        test_prediction.actual_outcome = ActualOutcome.OCCURRED
        test_prediction.actual_time = test_prediction.predicted_time
        test_prediction.accuracy_score = 1.0
        
        updated = await prediction_repository.update(test_prediction)
        assert updated.accuracy_score == 1.0
        
        # Test prediction with 12-hour difference
        test_prediction.actual_time = test_prediction.predicted_time + timedelta(hours=12)
        time_diff = 12 * 3600  # 12 hours in seconds
        max_diff = 48 * 3600  # 48 hours in seconds
        expected_accuracy = 1.0 - (time_diff / max_diff)
        test_prediction.accuracy_score = expected_accuracy
        
        updated = await prediction_repository.update(test_prediction)
        assert abs(updated.accuracy_score - expected_accuracy) < 0.01

    async def test_multiple_predictions_accuracy_tracking(
        self, prediction_repository, test_api
    ):
        """Test tracking accuracy for multiple predictions."""
        api, gateway_id = test_api
        now = datetime.utcnow()
        
        predictions = []
        
        # Create multiple predictions with different outcomes
        for i in range(3):
            prediction = Prediction(
                id=uuid4(),
                gateway_id=gateway_id,
                api_id=api.id,
                api_name=api.name,
                prediction_type=PredictionType.FAILURE,
                predicted_at=now,
                predicted_time=now + timedelta(hours=48),
                confidence_score=0.8 + (i * 0.05),
                severity=PredictionSeverity.HIGH,
                status=PredictionStatus.ACTIVE,
                contributing_factors=[],
                recommended_actions=[],
                actual_outcome=None,
                actual_time=None,
                accuracy_score=None,
                model_version="1.0.0",
                metadata={},
            )
            
            created = await prediction_repository.create(prediction)
            predictions.append(created)
        
        try:
            # Update with different outcomes
            outcomes = [
                (ActualOutcome.OCCURRED, 0.9),
                (ActualOutcome.PREVENTED, 0.95),
                (ActualOutcome.FALSE_ALARM, 0.0),
            ]
            
            for pred, (outcome, accuracy) in zip(predictions, outcomes):
                pred.actual_outcome = outcome
                pred.actual_time = now + timedelta(hours=48)
                pred.accuracy_score = accuracy
                pred.status = (
                    PredictionStatus.RESOLVED
                    if outcome != ActualOutcome.FALSE_ALARM
                    else PredictionStatus.FALSE_POSITIVE
                )
                await prediction_repository.update(pred)
            
            # Verify all predictions were tracked
            for pred, (outcome, accuracy) in zip(predictions, outcomes):
                retrieved = await prediction_repository.get(str(pred.id))
                assert retrieved.actual_outcome == outcome
                assert retrieved.accuracy_score == accuracy
        
        finally:
            # Cleanup
            for pred in predictions:
                try:
                    await prediction_repository.delete(str(pred.id))
                except Exception:
                    pass

    async def test_accuracy_reporting(
        self, prediction_repository, test_api
    ):
        """Test accuracy reporting and aggregation."""
        api, gateway_id = test_api
        now = datetime.utcnow()
        
        # Create predictions with known accuracy scores
        predictions = []
        accuracy_scores = [1.0, 0.9, 0.8, 0.7, 0.0]  # Average: 0.68
        
        for i, accuracy in enumerate(accuracy_scores):
            prediction = Prediction(
                id=uuid4(),
                gateway_id=gateway_id,
                api_id=api.id,
                api_name=api.name,
                prediction_type=PredictionType.FAILURE,
                predicted_at=now - timedelta(days=i+1),
                predicted_time=now - timedelta(days=i+1) + timedelta(hours=48),
                confidence_score=0.85,
                severity=PredictionSeverity.HIGH,
                status=PredictionStatus.RESOLVED,
                contributing_factors=[],
                recommended_actions=[],
                actual_outcome=ActualOutcome.OCCURRED if accuracy > 0 else ActualOutcome.FALSE_ALARM,
                actual_time=now - timedelta(days=i+1) + timedelta(hours=48),
                accuracy_score=accuracy,
                model_version="1.0.0",
                metadata={},
            )
            
            created = await prediction_repository.create(prediction)
            predictions.append(created)
        
        try:
            # Query predictions with accuracy scores
            resolved_predictions, _ = await prediction_repository.find_by_api(
                api_id=api.id,
                status=PredictionStatus.RESOLVED,
            )
            
            # Calculate average accuracy
            accuracies = [p.accuracy_score for p in resolved_predictions if p.accuracy_score is not None]
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
            
            # Verify accuracy reporting
            assert len(accuracies) >= 4  # At least 4 with non-zero accuracy
            assert 0.6 <= avg_accuracy <= 0.8  # Should be around 0.68
        
        finally:
            # Cleanup
            for pred in predictions:
                try:
                    await prediction_repository.delete(str(pred.id))
                except Exception:
                    pass

    async def test_expired_prediction_handling(
        self, prediction_repository, test_prediction
    ):
        """Test handling of expired predictions (no outcome recorded)."""
        # Simulate prediction expiration (predicted time passed, no outcome)
        expired_time = test_prediction.predicted_time + timedelta(hours=24)
        
        # Update prediction as expired
        test_prediction.status = PredictionStatus.EXPIRED
        test_prediction.actual_outcome = None
        test_prediction.actual_time = None
        test_prediction.accuracy_score = None
        
        # Update in repository
        updated = await prediction_repository.update(test_prediction)
        
        # Verify expired status
        assert updated.status == PredictionStatus.EXPIRED
        assert updated.actual_outcome is None
        assert updated.accuracy_score is None

# Made with Bob
