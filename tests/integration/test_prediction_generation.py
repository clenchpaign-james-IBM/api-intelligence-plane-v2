"""
Integration tests for prediction generation.

Tests the complete prediction generation workflow:
1. Create test API with metrics
2. Generate predictions using PredictionService
3. Verify predictions are stored in OpenSearch
4. Verify prediction attributes (confidence, severity, factors)
5. Verify prediction types (failure, degradation, capacity)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.app.db.repositories.prediction_repository import PredictionRepository
from backend.app.db.repositories.metrics_repository import MetricsRepository
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.services.prediction_service import PredictionService
from backend.app.models.prediction import (
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
)
from backend.app.models.base.metric import Metric, TimeBucket
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
    return PredictionRepository(opensearch_client)


@pytest.fixture
async def metrics_repository(opensearch_client):
    """Create Metrics repository instance."""
    return MetricsRepository(opensearch_client)


@pytest.fixture
async def api_repository(opensearch_client):
    """Create API repository instance."""
    return APIRepository(opensearch_client)


@pytest.fixture
async def prediction_service(
    prediction_repository, metrics_repository, api_repository
):
    """Create Prediction service instance."""
    return PredictionService(
        prediction_repository=prediction_repository,
        metrics_repository=metrics_repository,
        api_repository=api_repository,
        llm_service=None,  # No LLM for basic tests
    )


@pytest.fixture
async def test_api(api_repository):
    """Create a test API for prediction generation."""
    gateway_id = uuid4()
    api_id = uuid4()
    now = datetime.utcnow()
    
    api = API(
        id=api_id,
        gateway_id=gateway_id,
        name="Test Prediction API",
        version="1.0.0",
        base_path="/api/v1/test",
        endpoints=[],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.NONE,
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=now,
            last_seen_at=now,
            health_score=85.0,
        ),
        status=APIStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    
    created_api = await api_repository.create(api)
    yield created_api, gateway_id
    
    # Cleanup
    try:
        await api_repository.delete(str(created_api.id))
    except Exception:
        pass


@pytest.fixture
async def degrading_metrics(metrics_repository, test_api):
    """Create metrics showing degrading performance."""
    api, gateway_id = test_api
    now = datetime.utcnow()
    metrics = []
    
    # Create 24 hours of metrics with degrading performance
    for i in range(24):
        timestamp = now - timedelta(hours=23 - i)
        
        # Gradually increasing error rate (5% to 15%)
        error_rate = 5.0 + (i * 0.4)
        
        # Gradually increasing response time (1000ms to 2500ms)
        response_time_p95 = 1000 + (i * 60)
        
        # Gradually decreasing availability (99% to 93%)
        availability = 99.0 - (i * 0.25)
        
        metric = Metric(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api.id,
            timestamp=timestamp,
            time_bucket=TimeBucket.ONE_MINUTE,
            request_count=1000,
            success_count=int(1000 * (1 - error_rate / 100)),
            failure_count=int(1000 * error_rate / 100),
            error_rate=error_rate,
            response_time_avg=response_time_p95 * 0.7,
            response_time_p50=response_time_p95 * 0.8,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p95 * 1.2,
            response_time_min=response_time_p95 * 0.3,
            response_time_max=response_time_p95 * 1.5,
            gateway_time_avg=50.0,
            backend_time_avg=response_time_p95 * 0.6,
            cache_hit_rate=20.0,
            cache_hit_count=200,
            cache_miss_count=800,
            cache_bypass_count=0,
            total_data_size=1000000,
            avg_request_size=500,
            avg_response_size=500,
            status_2xx_count=int(1000 * (1 - error_rate / 100)),
            status_3xx_count=0,
            status_4xx_count=int(1000 * error_rate / 100 * 0.3),
            status_5xx_count=int(1000 * error_rate / 100 * 0.7),
            timeout_count=10,
            throughput=1000.0,
            availability=availability,
            status_codes={"200": int(1000 * (1 - error_rate / 100)), "500": int(1000 * error_rate / 100)},
        )
        
        created_metric = await metrics_repository.create(metric)
        metrics.append(created_metric)
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            await metrics_repository.delete(str(metric.id))
        except Exception:
            pass


@pytest.mark.asyncio
class TestPredictionGeneration:
    """Integration tests for prediction generation."""

    async def test_generate_failure_prediction(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test generation of failure prediction for degrading API."""
        api, gateway_id = test_api
        
        # Generate predictions
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        # Verify predictions were generated
        assert len(predictions) > 0, "Should generate at least one prediction"
        
        # Find failure prediction
        failure_predictions = [
            p for p in predictions if p.prediction_type == PredictionType.FAILURE
        ]
        assert len(failure_predictions) > 0, "Should generate failure prediction"
        
        failure_pred = failure_predictions[0]
        
        # Verify prediction attributes
        assert failure_pred.api_id == api.id
        assert failure_pred.gateway_id == gateway_id
        assert failure_pred.confidence_score >= 0.7
        assert failure_pred.status == PredictionStatus.ACTIVE
        assert failure_pred.severity in [
            PredictionSeverity.CRITICAL,
            PredictionSeverity.HIGH,
            PredictionSeverity.MEDIUM,
        ]
        
        # Verify contributing factors
        assert len(failure_pred.contributing_factors) > 0
        
        # Verify recommended actions
        assert len(failure_pred.recommended_actions) > 0
        
        # Verify prediction time is in future (24-48 hours)
        time_diff = failure_pred.predicted_time - failure_pred.predicted_at
        assert timedelta(hours=24) <= time_diff <= timedelta(hours=72)

    async def test_generate_degradation_prediction(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test generation of degradation prediction."""
        api, gateway_id = test_api
        
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.6
        )
        
        # Find degradation prediction
        degradation_predictions = [
            p for p in predictions if p.prediction_type == PredictionType.DEGRADATION
        ]
        
        if len(degradation_predictions) > 0:
            deg_pred = degradation_predictions[0]
            
            # Verify prediction attributes
            assert deg_pred.api_id == api.id
            assert deg_pred.confidence_score >= 0.6
            assert deg_pred.status == PredictionStatus.ACTIVE
            assert len(deg_pred.contributing_factors) > 0
            assert len(deg_pred.recommended_actions) > 0

    async def test_prediction_confidence_threshold(
        self, prediction_service, test_api, degrading_metrics
    ):
        """Test that predictions respect minimum confidence threshold."""
        api, gateway_id = test_api
        
        # Generate with high confidence threshold
        high_conf_predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.9
        )
        
        # Generate with low confidence threshold
        low_conf_predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.5
        )
        
        # Low threshold should generate more or equal predictions
        assert len(low_conf_predictions) >= len(high_conf_predictions)
        
        # All predictions should meet their threshold
        for pred in high_conf_predictions:
            assert pred.confidence_score >= 0.9
        
        for pred in low_conf_predictions:
            assert pred.confidence_score >= 0.5

    async def test_no_prediction_for_healthy_api(
        self, prediction_service, api_repository, metrics_repository, test_api
    ):
        """Test that no predictions are generated for healthy API."""
        api, gateway_id = test_api
        now = datetime.utcnow()
        
        # Create healthy metrics
        healthy_metrics = []
        for i in range(24):
            timestamp = now - timedelta(hours=23 - i)
            
            metric = Metric(
                id=uuid4(),
                gateway_id=gateway_id,
                api_id=api.id,
                timestamp=timestamp,
                time_bucket=TimeBucket.ONE_MINUTE,
                request_count=1000,
                success_count=995,
                failure_count=5,
                error_rate=0.5,  # Low error rate
                response_time_avg=100.0,
                response_time_p50=120.0,
                response_time_p95=200.0,  # Good response time
                response_time_p99=300.0,
                response_time_min=50.0,
                response_time_max=500.0,
                gateway_time_avg=30.0,
                backend_time_avg=70.0,
                cache_hit_rate=50.0,
                cache_hit_count=500,
                cache_miss_count=500,
                cache_bypass_count=0,
                total_data_size=1000000,
                avg_request_size=500,
                avg_response_size=500,
                status_2xx_count=995,
                status_3xx_count=0,
                status_4xx_count=3,
                status_5xx_count=2,
                timeout_count=0,
                throughput=1000.0,
                availability=99.5,  # High availability
                status_codes={"200": 995, "500": 5},
            )
            
            created_metric = await metrics_repository.create(metric)
            healthy_metrics.append(created_metric)
        
        try:
            # Generate predictions
            predictions = await prediction_service.generate_predictions_for_api(
                gateway_id=gateway_id,
                api_id=api.id,
                min_confidence=0.7
            )
            
            # Should generate no predictions for healthy API
            assert len(predictions) == 0, "Should not generate predictions for healthy API"
        
        finally:
            # Cleanup
            for metric in healthy_metrics:
                try:
                    await metrics_repository.delete(str(metric.id))
                except Exception:
                    pass

    async def test_prediction_persistence(
        self, prediction_service, prediction_repository, test_api, degrading_metrics
    ):
        """Test that predictions are persisted to OpenSearch."""
        api, gateway_id = test_api
        
        # Generate predictions
        predictions = await prediction_service.generate_predictions_for_api(
            gateway_id=gateway_id,
            api_id=api.id,
            min_confidence=0.7
        )
        
        assert len(predictions) > 0
        
        # Verify predictions can be retrieved from repository
        for prediction in predictions:
            retrieved = await prediction_repository.get(str(prediction.id))
            assert retrieved is not None
            assert retrieved.id == prediction.id
            assert retrieved.api_id == prediction.api_id
            assert retrieved.prediction_type == prediction.prediction_type
            
            # Cleanup
            try:
                await prediction_repository.delete(str(prediction.id))
            except Exception:
                pass

# Made with Bob
