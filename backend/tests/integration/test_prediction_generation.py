"""Integration tests for prediction generation.

Tests the prediction service with real OpenSearch data to verify:
- Prediction generation logic
- Contributing factor identification
- Confidence scoring
- Severity determination

Requires OpenSearch to be running and accessible.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.client import get_client
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.prediction_service import PredictionService
from app.models.base.metric import Metric
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.prediction import PredictionType, PredictionSeverity


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def opensearch_client():
    """Get OpenSearch client."""
    return get_client()


@pytest.fixture
def prediction_repository():
    """Create prediction repository."""
    return PredictionRepository()


@pytest.fixture
def metrics_repository():
    """Create metrics repository."""
    return MetricsRepository()


@pytest.fixture
def api_repository():
    """Create API repository."""
    return APIRepository()


@pytest.fixture
def prediction_service(prediction_repository, metrics_repository, api_repository):
    """Create prediction service with real repositories."""
    return PredictionService(
        prediction_repository=prediction_repository,
        metrics_repository=metrics_repository,
        api_repository=api_repository,
    )


@pytest.fixture
async def test_api(api_repository):
    """Create a test API in OpenSearch."""
    now = datetime.utcnow()
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="Test API for Predictions",
        version="1.0.0",
        base_path="/api/v1",
        endpoints=[
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint",
                parameters=[],
                response_codes=[200, 500],
            )
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.NONE,
        authentication_config=None,
        ownership=None,
        tags=["test"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=now,
        last_seen_at=now,
        status=APIStatus.ACTIVE,
        health_score=95.0,
        current_metrics=CurrentMetrics(
            response_time_p50=100.0,
            response_time_p95=200.0,
            response_time_p99=300.0,
            error_rate=0.01,
            throughput=10.0,
            availability=99.9,
            last_error=None,
            measured_at=now,
        ),
        metadata={},
    )
    
    # Store in OpenSearch
    await api_repository.create(api)
    
    yield api
    
    # Cleanup
    try:
        await api_repository.delete(api.id)
    except Exception:
        pass


@pytest.fixture
async def degrading_metrics(test_api, metrics_repository):
    """Create metrics showing degrading performance in OpenSearch."""
    now = datetime.utcnow()
    metrics = []
    
    # Generate 24 hours of metrics with degrading performance
    for i in range(24):
        timestamp = now - timedelta(hours=23-i)
        
        # Error rate increasing from 2% to 15%
        error_rate = 0.02 + (i * 0.0054)
        
        # Response time increasing from 100ms to 400ms
        response_time_p95 = 100 + (i * 12.5)
        
        # Availability decreasing from 99.9% to 94%
        availability = 99.9 - (i * 0.25)
        
        metric = Metric(
            id=uuid4(),
            api_id=test_api.id,
            gateway_id=test_api.gateway_id,
            timestamp=timestamp,
            response_time_p50=response_time_p95 * 0.6,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p95 * 1.2,
            error_rate=error_rate,
            error_count=int(error_rate * 1000),
            request_count=1000,
            throughput=1000 / 60,
            availability=availability,
            status_codes={"200": int((1-error_rate) * 1000), "500": int(error_rate * 1000)},
            endpoint_metrics=None,
            metadata=None,
        )
        
        # Store in OpenSearch
        await metrics_repository.create(metric)
        metrics.append(metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            await metrics_repository.delete(metric.id)
        except Exception:
            pass


@pytest.fixture
async def stable_metrics(test_api, metrics_repository):
    """Create metrics showing stable performance in OpenSearch."""
    now = datetime.utcnow()
    metrics = []
    
    # Generate 24 hours of stable metrics
    for i in range(24):
        timestamp = now - timedelta(hours=23-i)
        
        metric = Metric(
            id=uuid4(),
            api_id=test_api.id,
            gateway_id=test_api.gateway_id,
            timestamp=timestamp,
            response_time_p50=80,
            response_time_p95=150,
            response_time_p99=200,
            error_rate=0.01,
            error_count=10,
            request_count=1000,
            throughput=16.67,
            availability=99.9,
            status_codes={"200": 990, "500": 10},
            endpoint_metrics=None,
            metadata=None,
        )
        
        # Store in OpenSearch
        await metrics_repository.create(metric)
        metrics.append(metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            await metrics_repository.delete(metric.id)
        except Exception:
            pass


@pytest.mark.asyncio
class TestPredictionGeneration:
    """Test prediction generation with real data."""
    
    async def test_generate_predictions_for_degrading_api(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test that degrading metrics generate predictions."""
        # Generate predictions for the test API
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.7
        )
        
        # Should generate at least one prediction
        assert len(predictions) > 0
        
        # Find failure or degradation prediction
        critical_predictions = [
            p for p in predictions 
            if p.prediction_type in [PredictionType.FAILURE, PredictionType.DEGRADATION]
            and p.confidence_score >= 0.7
        ]
        assert len(critical_predictions) > 0
        
        prediction = critical_predictions[0]
        
        # Verify prediction properties
        assert prediction.api_id == test_api.id
        assert prediction.confidence_score >= 0.7
        assert prediction.severity in [
            PredictionSeverity.HIGH, 
            PredictionSeverity.CRITICAL,
            PredictionSeverity.MEDIUM
        ]
        
        # Verify time window (24-48 hours)
        time_diff = (prediction.predicted_time - prediction.predicted_at).total_seconds()
        assert 24 * 3600 <= time_diff <= 48 * 3600
        
        # Verify contributing factors
        assert len(prediction.contributing_factors) > 0
        
        # Should identify error rate or response time as factors
        factor_names = [f.factor.lower() for f in prediction.contributing_factors]
        assert any('error' in name or 'response' in name for name in factor_names)
        
        # Verify recommended actions
        assert len(prediction.recommended_actions) > 0
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_service.prediction_repo.delete(pred.id)
            except Exception:
                pass
    
    async def test_no_predictions_for_stable_api(
        self, prediction_service, test_api, stable_metrics
    ):
        """Test that stable metrics don't generate high-confidence predictions."""
        # Generate predictions for the stable API
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.7
        )
        
        # Should not generate high-confidence critical predictions
        critical_predictions = [
            p for p in predictions 
            if p.confidence_score >= 0.7
            and p.severity in [PredictionSeverity.HIGH, PredictionSeverity.CRITICAL]
        ]
        assert len(critical_predictions) == 0
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_service.prediction_repo.delete(pred.id)
            except Exception:
                pass
    
    async def test_prediction_persistence(
        self, prediction_service, prediction_repository, test_api, degrading_metrics
    ):
        """Test that predictions are stored in OpenSearch."""
        # Generate predictions
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.7
        )
        
        assert len(predictions) > 0
        prediction_id = predictions[0].id
        
        # Retrieve from repository
        stored_prediction = await prediction_repository.get(prediction_id)
        
        assert stored_prediction is not None
        assert stored_prediction.id == prediction_id
        assert stored_prediction.api_id == test_api.id
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_repository.delete(pred.id)
            except Exception:
                pass
    
    async def test_contributing_factors_structure(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test that contributing factors have correct structure."""
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.7
        )
        
        assert len(predictions) > 0
        prediction = predictions[0]
        
        # Verify factor structure
        for factor in prediction.contributing_factors:
            assert factor.factor is not None
            assert factor.current_value is not None
            assert factor.threshold is not None
            assert factor.trend in ['increasing', 'decreasing', 'stable', 'volatile']
            assert 0 <= factor.weight <= 1
        
        # Verify factors are sorted by weight
        weights = [f.weight for f in prediction.contributing_factors]
        assert weights == sorted(weights, reverse=True)
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_service.prediction_repo.delete(pred.id)
            except Exception:
                pass
    
    async def test_confidence_scoring(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test confidence score calculation."""
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.5
        )
        
        assert len(predictions) > 0
        
        for prediction in predictions:
            # Confidence should be sum of factor weights
            expected_confidence = sum(f.weight for f in prediction.contributing_factors)
            assert abs(prediction.confidence_score - expected_confidence) < 0.01
            
            # Confidence should be in valid range
            assert 0 <= prediction.confidence_score <= 1
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_service.prediction_repo.delete(pred.id)
            except Exception:
                pass
    
    async def test_severity_determination(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test severity is correctly determined from confidence."""
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            min_confidence=0.5
        )
        
        assert len(predictions) > 0
        
        for prediction in predictions:
            # Verify severity matches confidence thresholds
            if prediction.confidence_score >= 0.9:
                assert prediction.severity == PredictionSeverity.CRITICAL
            elif prediction.confidence_score >= 0.8:
                assert prediction.severity == PredictionSeverity.HIGH
            elif prediction.confidence_score >= 0.7:
                assert prediction.severity == PredictionSeverity.MEDIUM
            else:
                assert prediction.severity == PredictionSeverity.LOW
        
        # Cleanup
        for pred in predictions:
            try:
                await prediction_service.prediction_repo.delete(pred.id)
            except Exception:
                pass


@pytest.mark.asyncio
class TestPredictionAccuracy:
    """Test prediction accuracy tracking."""
    
    async def test_accuracy_calculation(self, prediction_service):
        """Test accuracy score calculation."""
        # Prediction made at T0, predicted for T0+36h
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=36)
        
        # Event occurred at T0+35h (1 hour early)
        actual_time = predicted_at + timedelta(hours=35)
        
        # Calculate accuracy: 1 - |1h| / 48h = 1 - 0.0208 = 0.979
        accuracy = prediction_service._calculate_accuracy(
            predicted_time=predicted_time,
            actual_time=actual_time
        )
        
        expected_accuracy = 1 - (1 / 48)
        assert abs(accuracy - expected_accuracy) < 0.01
    
    async def test_accuracy_perfect_prediction(self, prediction_service):
        """Test accuracy for perfect prediction."""
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=36)
        actual_time = predicted_time  # Exact match
        
        accuracy = prediction_service._calculate_accuracy(
            predicted_time=predicted_time,
            actual_time=actual_time
        )
        
        assert accuracy == 1.0
    
    async def test_accuracy_worst_case(self, prediction_service):
        """Test accuracy for worst case (48h off)."""
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=36)
        actual_time = predicted_at + timedelta(hours=84)  # 48h late
        
        accuracy = prediction_service._calculate_accuracy(
            predicted_time=predicted_time,
            actual_time=actual_time
        )
        
        assert accuracy == 0.0


# Made with Bob