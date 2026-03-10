"""Validation tests for User Story 2: Predict and Prevent API Failures.

Simulates real-world scenarios to validate that the system can:
1. Detect degrading API performance
2. Generate predictions 24-48 hours in advance
3. Provide actionable recommendations
4. Track prediction accuracy

Requires OpenSearch to be running and accessible.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.models.metric import Metric
from app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)
from app.models.prediction import PredictionType, PredictionSeverity, PredictionStatus


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


async def create_test_api(api_repository, name: str):
    """Helper to create a test API."""
    now = datetime.utcnow()
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name=name,
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
        tags=["validation-test"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
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
    return api


async def create_degrading_metrics(api, metrics_repository, hours=24, severity="high"):
    """Helper to create degrading metrics with different severity levels."""
    now = datetime.utcnow()
    metrics = []
    
    # Adjust degradation rate based on severity
    if severity == "critical":
        error_rate_start, error_rate_end = 0.05, 0.25
        response_time_start, response_time_end = 200, 800
        availability_start, availability_end = 99.5, 90.0
    elif severity == "high":
        error_rate_start, error_rate_end = 0.02, 0.15
        response_time_start, response_time_end = 100, 400
        availability_start, availability_end = 99.9, 94.0
    else:  # medium
        error_rate_start, error_rate_end = 0.01, 0.08
        response_time_start, response_time_end = 80, 250
        availability_start, availability_end = 99.9, 97.0
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours-1-i)
        
        # Linear degradation
        progress = i / (hours - 1) if hours > 1 else 0
        error_rate = error_rate_start + (error_rate_end - error_rate_start) * progress
        response_time_p95 = response_time_start + (response_time_end - response_time_start) * progress
        availability = availability_start - (availability_start - availability_end) * progress
        
        metric = Metric(
            id=uuid4(),
            api_id=api.id,
            gateway_id=api.gateway_id,
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
    
    return metrics


@pytest.mark.asyncio
class TestUserStory2Validation:
    """Validation tests for User Story 2 acceptance criteria."""
    
    async def test_scenario_1_gradual_degradation_detection(
        self, client, api_repository, metrics_repository, prediction_repository
    ):
        """
        Scenario: API experiencing gradual performance degradation
        Expected: System detects trend and predicts failure 24-48h in advance
        """
        # Setup: Create API with degrading metrics over 24 hours
        api = await create_test_api(api_repository, "Gradual Degradation API")
        metrics = await create_degrading_metrics(api, metrics_repository, hours=24, severity="high")
        
        try:
            # Action: Generate predictions
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(api.id),
                    "min_confidence": 0.7
                }
            )
            
            # Validation
            assert response.status_code == 200
            data = response.json()
            predictions = data["predictions"]
            
            # Should generate at least one high-confidence prediction
            assert len(predictions) > 0, "No predictions generated for degrading API"
            
            # Find failure or degradation predictions
            critical_predictions = [
                p for p in predictions
                if p["prediction_type"] in ["failure", "degradation"]
                and p["confidence_score"] >= 0.7
            ]
            
            assert len(critical_predictions) > 0, "No critical predictions generated"
            
            prediction = critical_predictions[0]
            
            # Verify prediction time window (24-48 hours)
            predicted_at = datetime.fromisoformat(prediction["predicted_at"].replace('Z', '+00:00'))
            predicted_time = datetime.fromisoformat(prediction["predicted_time"].replace('Z', '+00:00'))
            time_diff_hours = (predicted_time - predicted_at).total_seconds() / 3600
            
            assert 24 <= time_diff_hours <= 48, \
                f"Prediction time window {time_diff_hours}h not in 24-48h range"
            
            # Verify contributing factors identified
            assert len(prediction["contributing_factors"]) > 0, \
                "No contributing factors identified"
            
            # Verify recommended actions provided
            assert len(prediction["recommended_actions"]) > 0, \
                "No recommended actions provided"
            
            # Verify severity appropriate for degradation level
            assert prediction["severity"] in ["high", "critical"], \
                f"Unexpected severity: {prediction['severity']}"
            
            print(f"✓ Scenario 1 PASSED: Detected degradation with {time_diff_hours:.1f}h advance warning")
            
        finally:
            # Cleanup
            for metric in metrics:
                try:
                    await metrics_repository.delete(metric.id)
                except Exception:
                    pass
            
            # Clean up predictions
            response = client.get("/api/v1/predictions", params={"api_id": str(api.id)})
            if response.status_code == 200:
                for pred in response.json()["predictions"]:
                    try:
                        await prediction_repository.delete(pred["id"])
                    except Exception:
                        pass
            
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass
    
    async def test_scenario_2_sudden_spike_detection(
        self, client, api_repository, metrics_repository, prediction_repository
    ):
        """
        Scenario: API experiencing sudden error rate spike
        Expected: System detects anomaly and generates high-severity prediction
        """
        # Setup: Create API with sudden spike in last 6 hours
        api = await create_test_api(api_repository, "Sudden Spike API")
        
        now = datetime.utcnow()
        metrics = []
        
        # First 18 hours: stable
        for i in range(18):
            timestamp = now - timedelta(hours=23-i)
            metric = Metric(
                id=uuid4(),
                api_id=api.id,
                gateway_id=api.gateway_id,
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
            await metrics_repository.create(metric)
            metrics.append(metric)
        
        # Last 6 hours: sudden spike
        for i in range(6):
            timestamp = now - timedelta(hours=5-i)
            error_rate = 0.15 + (i * 0.02)  # 15% to 25%
            metric = Metric(
                id=uuid4(),
                api_id=api.id,
                gateway_id=api.gateway_id,
                timestamp=timestamp,
                response_time_p50=200,
                response_time_p95=400,
                response_time_p99=600,
                error_rate=error_rate,
                error_count=int(error_rate * 1000),
                request_count=1000,
                throughput=16.67,
                availability=95.0,
                status_codes={"200": int((1-error_rate) * 1000), "500": int(error_rate * 1000)},
                endpoint_metrics=None,
                metadata=None,
            )
            await metrics_repository.create(metric)
            metrics.append(metric)
        
        try:
            # Action: Generate predictions
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(api.id),
                    "min_confidence": 0.7
                }
            )
            
            # Validation
            assert response.status_code == 200
            predictions = response.json()["predictions"]
            
            # Should detect the spike
            assert len(predictions) > 0, "No predictions for sudden spike"
            
            # Should have high severity
            high_severity_predictions = [
                p for p in predictions
                if p["severity"] in ["high", "critical"]
            ]
            
            assert len(high_severity_predictions) > 0, "No high-severity predictions for spike"
            
            # Should identify error rate as contributing factor
            prediction = high_severity_predictions[0]
            factor_names = [f["factor"].lower() for f in prediction["contributing_factors"]]
            assert any("error" in name for name in factor_names), \
                "Error rate not identified as contributing factor"
            
            print(f"✓ Scenario 2 PASSED: Detected sudden spike with {prediction['severity']} severity")
            
        finally:
            # Cleanup
            for metric in metrics:
                try:
                    await metrics_repository.delete(metric.id)
                except Exception:
                    pass
            
            response = client.get("/api/v1/predictions", params={"api_id": str(api.id)})
            if response.status_code == 200:
                for pred in response.json()["predictions"]:
                    try:
                        await prediction_repository.delete(pred["id"])
                    except Exception:
                        pass
            
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass
    
    async def test_scenario_3_multiple_factor_correlation(
        self, client, api_repository, metrics_repository, prediction_repository
    ):
        """
        Scenario: API degrading across multiple metrics simultaneously
        Expected: System correlates factors and generates comprehensive prediction
        """
        # Setup: Create API with multi-factor degradation
        api = await create_test_api(api_repository, "Multi-Factor Degradation API")
        metrics = await create_degrading_metrics(api, metrics_repository, hours=24, severity="critical")
        
        try:
            # Action: Generate predictions
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(api.id),
                    "min_confidence": 0.7
                }
            )
            
            # Validation
            assert response.status_code == 200
            predictions = response.json()["predictions"]
            assert len(predictions) > 0
            
            prediction = predictions[0]
            factors = prediction["contributing_factors"]
            
            # Should identify multiple contributing factors
            assert len(factors) >= 2, "Should identify multiple contributing factors"
            
            # Should include error rate, response time, or availability
            factor_types = {f["factor"].lower() for f in factors}
            expected_factors = {"error", "response", "availability"}
            identified = sum(1 for expected in expected_factors 
                           if any(expected in ft for ft in factor_types))
            
            assert identified >= 2, \
                f"Should identify at least 2 of {expected_factors}, found {factor_types}"
            
            # Factors should be weighted
            weights = [f["weight"] for f in factors]
            assert all(0 < w <= 1 for w in weights), "Invalid factor weights"
            assert weights == sorted(weights, reverse=True), "Factors not sorted by weight"
            
            print(f"✓ Scenario 3 PASSED: Identified {len(factors)} contributing factors")
            
        finally:
            # Cleanup
            for metric in metrics:
                try:
                    await metrics_repository.delete(metric.id)
                except Exception:
                    pass
            
            response = client.get("/api/v1/predictions", params={"api_id": str(api.id)})
            if response.status_code == 200:
                for pred in response.json()["predictions"]:
                    try:
                        await prediction_repository.delete(pred["id"])
                    except Exception:
                        pass
            
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass
    
    async def test_scenario_4_actionable_recommendations(
        self, client, api_repository, metrics_repository, prediction_repository
    ):
        """
        Scenario: System generates predictions with actionable recommendations
        Expected: Recommendations are specific, relevant, and actionable
        """
        # Setup
        api = await create_test_api(api_repository, "Recommendations Test API")
        metrics = await create_degrading_metrics(api, metrics_repository, hours=24, severity="high")
        
        try:
            # Action
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(api.id),
                    "min_confidence": 0.7
                }
            )
            
            # Validation
            assert response.status_code == 200
            predictions = response.json()["predictions"]
            assert len(predictions) > 0
            
            prediction = predictions[0]
            actions = prediction["recommended_actions"]
            
            # Should provide multiple recommendations
            assert len(actions) >= 2, "Should provide at least 2 recommendations"
            
            # Recommendations should be non-empty strings
            assert all(isinstance(a, str) and len(a) > 10 for a in actions), \
                "Recommendations should be meaningful strings"
            
            # Should mention specific actions (scale, investigate, monitor, etc.)
            action_keywords = ["scale", "investigate", "monitor", "increase", "check", 
                             "review", "optimize", "alert", "capacity"]
            action_text = " ".join(actions).lower()
            found_keywords = [kw for kw in action_keywords if kw in action_text]
            
            assert len(found_keywords) >= 1, \
                f"Recommendations should include actionable keywords, found: {found_keywords}"
            
            print(f"✓ Scenario 4 PASSED: Generated {len(actions)} actionable recommendations")
            
        finally:
            # Cleanup
            for metric in metrics:
                try:
                    await metrics_repository.delete(metric.id)
                except Exception:
                    pass
            
            response = client.get("/api/v1/predictions", params={"api_id": str(api.id)})
            if response.status_code == 200:
                for pred in response.json()["predictions"]:
                    try:
                        await prediction_repository.delete(pred["id"])
                    except Exception:
                        pass
            
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass
    
    async def test_scenario_5_no_false_positives_for_stable_apis(
        self, client, api_repository, metrics_repository, prediction_repository
    ):
        """
        Scenario: Stable API with no degradation
        Expected: No high-confidence predictions generated (avoid false positives)
        """
        # Setup: Create API with stable metrics
        api = await create_test_api(api_repository, "Stable API")
        
        now = datetime.utcnow()
        metrics = []
        
        for i in range(24):
            timestamp = now - timedelta(hours=23-i)
            metric = Metric(
                id=uuid4(),
                api_id=api.id,
                gateway_id=api.gateway_id,
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
            await metrics_repository.create(metric)
            metrics.append(metric)
        
        try:
            # Action
            response = client.post(
                "/api/v1/predictions/generate",
                json={
                    "api_id": str(api.id),
                    "min_confidence": 0.7
                }
            )
            
            # Validation
            assert response.status_code == 200
            predictions = response.json()["predictions"]
            
            # Should not generate high-confidence critical predictions
            critical_predictions = [
                p for p in predictions
                if p["confidence_score"] >= 0.7
                and p["severity"] in ["high", "critical"]
            ]
            
            assert len(critical_predictions) == 0, \
                f"Generated {len(critical_predictions)} false positive predictions for stable API"
            
            print("✓ Scenario 5 PASSED: No false positives for stable API")
            
        finally:
            # Cleanup
            for metric in metrics:
                try:
                    await metrics_repository.delete(metric.id)
                except Exception:
                    pass
            
            response = client.get("/api/v1/predictions", params={"api_id": str(api.id)})
            if response.status_code == 200:
                for pred in response.json()["predictions"]:
                    try:
                        await prediction_repository.delete(pred["id"])
                    except Exception:
                        pass
            
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass


# Made with Bob