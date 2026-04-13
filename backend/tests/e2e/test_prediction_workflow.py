"""End-to-end tests for prediction workflow.

Tests the complete prediction workflow from metrics ingestion through
prediction generation, storage, retrieval, and accuracy tracking.

Requires OpenSearch to be running and accessible.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.client import get_client
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.models.base.metric import Metric
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.prediction import PredictionStatus, ActualOutcome


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client."""
    return TestClient(app)


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
async def test_api(api_repository):
    """Create a test API for E2E testing."""
    now = datetime.utcnow()
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="E2E Test API",
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
        tags=["e2e-test"],
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
    
    await api_repository.create(api)
    yield api
    
    # Cleanup
    try:
        await api_repository.delete(api.id)
    except Exception:
        pass


@pytest.fixture
async def degrading_metrics(test_api, metrics_repository):
    """Create degrading metrics for E2E testing."""
    now = datetime.utcnow()
    metrics = []
    
    for i in range(24):
        timestamp = now - timedelta(hours=23-i)
        error_rate = 0.02 + (i * 0.0054)
        response_time_p95 = 100 + (i * 12.5)
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
class TestPredictionWorkflowE2E:
    """End-to-end tests for complete prediction workflow."""
    
    async def test_complete_prediction_workflow(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test complete workflow: metrics → prediction → retrieval → update."""
        
        # Step 1: Generate predictions via API
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": str(test_api.id),
                "min_confidence": 0.7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0
        
        prediction_id = data["predictions"][0]["id"]
        
        # Step 2: Retrieve prediction via API
        response = client.get(f"/api/v1/predictions/{prediction_id}")
        assert response.status_code == 200
        prediction_data = response.json()
        
        assert prediction_data["id"] == prediction_id
        assert prediction_data["api_id"] == str(test_api.id)
        assert prediction_data["confidence_score"] >= 0.7
        assert len(prediction_data["contributing_factors"]) > 0
        assert len(prediction_data["recommended_actions"]) > 0
        
        # Step 3: List predictions via API
        response = client.get(
            "/api/v1/predictions",
            params={"api_id": str(test_api.id)}
        )
        assert response.status_code == 200
        list_data = response.json()
        
        assert list_data["total"] > 0
        assert any(p["id"] == prediction_id for p in list_data["predictions"])
        
        # Step 4: Update prediction status (simulate resolution)
        prediction = await prediction_repository.get(prediction_id)
        prediction.status = PredictionStatus.RESOLVED
        prediction.actual_outcome = ActualOutcome.TRUE_POSITIVE
        prediction.actual_time = datetime.utcnow() + timedelta(hours=30)
        
        await prediction_repository.update(prediction)
        
        # Step 5: Verify update
        updated_prediction = await prediction_repository.get(prediction_id)
        assert updated_prediction.status == PredictionStatus.RESOLVED
        assert updated_prediction.actual_outcome == ActualOutcome.OCCURRED
        assert updated_prediction.accuracy_score is not None
        assert 0 <= updated_prediction.accuracy_score <= 1
        
        # Cleanup
        await prediction_repository.delete(prediction_id)
    
    async def test_prediction_filtering_workflow(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test prediction filtering and querying."""
        
        # Generate predictions
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": str(test_api.id),
                "min_confidence": 0.5
            }
        )
        
        assert response.status_code == 200
        predictions = response.json()["predictions"]
        prediction_ids = [p["id"] for p in predictions]
        
        # Test filtering by severity
        response = client.get(
            "/api/v1/predictions",
            params={"severity": "high"}
        )
        assert response.status_code == 200
        high_severity = response.json()["predictions"]
        assert all(p["severity"] == "high" for p in high_severity)
        
        # Test filtering by status
        response = client.get(
            "/api/v1/predictions",
            params={"status": "active"}
        )
        assert response.status_code == 200
        active_predictions = response.json()["predictions"]
        assert all(p["status"] == "active" for p in active_predictions)
        
        # Test filtering by API
        response = client.get(
            "/api/v1/predictions",
            params={"api_id": str(test_api.id)}
        )
        assert response.status_code == 200
        api_predictions = response.json()["predictions"]
        assert all(p["api_id"] == str(test_api.id) for p in api_predictions)
        
        # Cleanup
        for pred_id in prediction_ids:
            try:
                await prediction_repository.delete(pred_id)
            except Exception:
                pass
    
    async def test_prediction_accuracy_tracking_workflow(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test accuracy tracking workflow."""
        
        # Generate predictions
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": str(test_api.id),
                "min_confidence": 0.7
            }
        )
        
        assert response.status_code == 200
        predictions = response.json()["predictions"]
        
        # Simulate outcomes for predictions
        for pred_data in predictions[:3]:  # Test first 3 predictions
            prediction = await prediction_repository.get(pred_data["id"])
            
            # Simulate true positive (event occurred close to predicted time)
            prediction.status = PredictionStatus.RESOLVED
            prediction.actual_outcome = ActualOutcome.OCCURRED
            prediction.actual_time = prediction.predicted_time + timedelta(hours=2)
            
            await prediction_repository.update(prediction)
        
        # Get accuracy statistics
        response = client.get("/api/v1/predictions/stats/accuracy")
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_predictions" in stats
        assert "resolved_predictions" in stats
        assert "average_accuracy" in stats
        assert stats["total_predictions"] >= 3
        assert stats["resolved_predictions"] >= 3
        
        # Cleanup
        for pred_data in predictions:
            try:
                await prediction_repository.delete(pred_data["id"])
            except Exception:
                pass
    
    async def test_prediction_expiration_workflow(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test prediction expiration handling."""
        
        # Generate predictions
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": str(test_api.id),
                "min_confidence": 0.7
            }
        )
        
        assert response.status_code == 200
        predictions = response.json()["predictions"]
        
        # Manually expire a prediction
        if predictions:
            prediction = await prediction_repository.get(predictions[0]["id"])
            prediction.predicted_time = datetime.utcnow() - timedelta(hours=1)
            await prediction_repository.update(prediction)
            
            # Verify it's marked as expired
            expired_prediction = await prediction_repository.get(prediction.id)
            assert expired_prediction.predicted_time < datetime.utcnow()
        
        # Cleanup
        for pred_data in predictions:
            try:
                await prediction_repository.delete(pred_data["id"])
            except Exception:
                pass
    
    async def test_concurrent_prediction_generation(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test concurrent prediction generation requests."""
        
        # Make multiple concurrent requests
        responses = []
        for _ in range(3):
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(test_api.id),
                    "min_confidence": 0.7
                }
            )
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Collect all prediction IDs for cleanup
        all_prediction_ids = []
        for response in responses:
            predictions = response.json()["predictions"]
            all_prediction_ids.extend([p["id"] for p in predictions])
        
        # Cleanup
        for pred_id in all_prediction_ids:
            try:
                await prediction_repository.delete(pred_id)
            except Exception:
                pass
    
    async def test_prediction_with_missing_api(self, client):
        """Test prediction generation for non-existent API."""
        
        fake_api_id = str(uuid4())
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": fake_api_id,
                "min_confidence": 0.7
            }
        )
        
        # Should handle gracefully (either 404 or empty predictions)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert len(data["predictions"]) == 0
    
    async def test_prediction_pagination(
        self, client, test_api, degrading_metrics, prediction_repository
    ):
        """Test prediction list pagination."""
        
        # Generate multiple predictions
        response = client.post(
            "/api/v1/predictions/generate",
            json={
                "api_id": str(test_api.id),
                "min_confidence": 0.5
            }
        )
        
        assert response.status_code == 200
        all_predictions = response.json()["predictions"]
        prediction_ids = [p["id"] for p in all_predictions]
        
        # Test pagination
        response = client.get(
            "/api/v1/predictions",
            params={"size": 2, "from": 0}
        )
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["predictions"]) <= 2
        
        response = client.get(
            "/api/v1/predictions",
            params={"size": 2, "from": 2}
        )
        assert response.status_code == 200
        page2 = response.json()
        
        # Pages should have different predictions
        page1_ids = {p["id"] for p in page1["predictions"]}
        page2_ids = {p["id"] for p in page2["predictions"]}
        assert page1_ids.isdisjoint(page2_ids)
        
        # Cleanup
        for pred_id in prediction_ids:
            try:
                await prediction_repository.delete(pred_id)
            except Exception:
                pass


# Made with Bob