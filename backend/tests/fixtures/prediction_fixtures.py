"""
Test Fixtures for Prediction Tests

Provides reusable test data and fixtures for prediction-related tests.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import List

from app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
    ActualOutcome,
    ContributingFactor,
    ContributingFactorType,
)
from app.models.metric import Metric
from app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)


@pytest.fixture
def sample_api_id() -> UUID:
    """Generate a sample API ID."""
    return uuid4()


@pytest.fixture
def sample_gateway_id() -> UUID:
    """Generate a sample gateway ID."""
    return uuid4()


@pytest.fixture
def sample_contributing_factors() -> List[ContributingFactor]:
    """Generate sample contributing factors."""
    return [
        ContributingFactor(
            factor=ContributingFactorType.INCREASING_ERROR_RATE,
            current_value=0.15,
            threshold=0.10,
            trend="increasing",
            weight=0.4,
        ),
        ContributingFactor(
            factor=ContributingFactorType.DEGRADING_RESPONSE_TIME,
            current_value=450.0,
            threshold=300.0,
            trend="increasing",
            weight=0.3,
        ),
        ContributingFactor(
            factor=ContributingFactorType.DECLINING_AVAILABILITY,
            current_value=94.5,
            threshold=95.0,
            trend="decreasing",
            weight=0.2,
        ),
    ]


@pytest.fixture
def sample_prediction(sample_api_id, sample_contributing_factors) -> Prediction:
    """Generate a sample prediction."""
    now = datetime.utcnow()
    return Prediction(
        id=uuid4(),
        api_id=sample_api_id,
        prediction_type=PredictionType.FAILURE,
        predicted_at=now,
        predicted_time=now + timedelta(hours=36),
        confidence_score=0.85,
        severity=PredictionSeverity.HIGH,
        status=PredictionStatus.ACTIVE,
        contributing_factors=sample_contributing_factors,
        recommended_actions=[
            "Scale up infrastructure resources",
            "Review error logs for root cause",
            "Enable circuit breaker pattern",
        ],
        actual_outcome=None,
        actual_time=None,
        accuracy_score=None,
        model_version="1.0.0",
        metadata={"test": True},
    )


@pytest.fixture
def critical_prediction(sample_api_id) -> Prediction:
    """Generate a critical severity prediction."""
    now = datetime.utcnow()
    return Prediction(
        id=uuid4(),
        api_id=sample_api_id,
        prediction_type=PredictionType.FAILURE,
        predicted_at=now,
        predicted_time=now + timedelta(hours=30),
        confidence_score=0.95,
        severity=PredictionSeverity.CRITICAL,
        status=PredictionStatus.ACTIVE,
        contributing_factors=[
            ContributingFactor(
                factor=ContributingFactorType.INCREASING_ERROR_RATE,
                current_value=0.25,
                threshold=0.10,
                trend="increasing",
                weight=0.5,
            ),
            ContributingFactor(
                factor=ContributingFactorType.DEGRADING_RESPONSE_TIME,
                current_value=800.0,
                threshold=300.0,
                trend="increasing",
                weight=0.45,
            ),
        ],
        recommended_actions=[
            "IMMEDIATE: Scale infrastructure",
            "IMMEDIATE: Enable circuit breaker",
            "IMMEDIATE: Alert on-call team",
        ],
        actual_outcome=None,
        actual_time=None,
        accuracy_score=None,
        model_version="1.0.0",
        metadata={"test": True, "severity": "critical"},
    )


@pytest.fixture
def resolved_prediction(sample_api_id) -> Prediction:
    """Generate a resolved prediction with outcome."""
    now = datetime.utcnow()
    predicted_at = now - timedelta(hours=48)
    predicted_time = predicted_at + timedelta(hours=36)
    actual_time = predicted_at + timedelta(hours=35)
    
    return Prediction(
        id=uuid4(),
        api_id=sample_api_id,
        prediction_type=PredictionType.DEGRADATION,
        predicted_at=predicted_at,
        predicted_time=predicted_time,
        confidence_score=0.80,
        severity=PredictionSeverity.MEDIUM,
        status=PredictionStatus.RESOLVED,
        contributing_factors=[
            ContributingFactor(
                factor=ContributingFactorType.INCREASING_ERROR_RATE,
                current_value=0.08,
                threshold=0.05,
                trend="increasing",
                weight=0.5,
            ),
            ContributingFactor(
                factor=ContributingFactorType.DEGRADING_RESPONSE_TIME,
                current_value=250.0,
                threshold=200.0,
                trend="increasing",
                weight=0.3,
            ),
        ],
        recommended_actions=[
            "Monitor closely",
            "Review recent changes",
        ],
        actual_outcome=ActualOutcome.OCCURRED,
        actual_time=actual_time,
        accuracy_score=0.979,  # 1 - (1h / 48h)
        model_version="1.0.0",
        metadata={"test": True, "resolved": True},
    )


@pytest.fixture
def sample_stable_metric(sample_api_id, sample_gateway_id) -> Metric:
    """Generate a sample stable metric."""
    return Metric(
        id=uuid4(),
        api_id=sample_api_id,
        gateway_id=sample_gateway_id,
        timestamp=datetime.utcnow(),
        response_time_p50=80.0,
        response_time_p95=150.0,
        response_time_p99=200.0,
        error_rate=0.01,
        error_count=10,
        request_count=1000,
        throughput=16.67,
        availability=99.9,
        status_codes={"200": 990, "500": 10},
        endpoint_metrics=None,
        metadata={"test": True},
    )


@pytest.fixture
def sample_degrading_metric(sample_api_id, sample_gateway_id) -> Metric:
    """Generate a sample degrading metric."""
    return Metric(
        id=uuid4(),
        api_id=sample_api_id,
        gateway_id=sample_gateway_id,
        timestamp=datetime.utcnow(),
        response_time_p50=200.0,
        response_time_p95=400.0,
        response_time_p99=600.0,
        error_rate=0.15,
        error_count=150,
        request_count=1000,
        throughput=16.67,
        availability=94.0,
        status_codes={"200": 850, "500": 150},
        endpoint_metrics=None,
        metadata={"test": True, "degrading": True},
    )


@pytest.fixture
def sample_test_api(sample_api_id, sample_gateway_id) -> API:
    """Generate a sample test API."""
    now = datetime.utcnow()
    return API(
        id=sample_api_id,
        gateway_id=sample_gateway_id,
        name="Test API",
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
        metadata={"test": True},
    )


def create_prediction_with_severity(
    api_id: UUID,
    severity: PredictionSeverity,
    hours_ahead: int = 36
) -> Prediction:
    """
    Helper function to create a prediction with specific severity.
    
    Args:
        api_id: API ID for the prediction
        severity: Desired severity level
        hours_ahead: Hours ahead for predicted_time
    
    Returns:
        Prediction instance
    """
    now = datetime.utcnow()
    
    # Map severity to confidence
    confidence_map = {
        PredictionSeverity.CRITICAL: 0.95,
        PredictionSeverity.HIGH: 0.85,
        PredictionSeverity.MEDIUM: 0.75,
        PredictionSeverity.LOW: 0.60,
    }
    
    # Map severity to prediction type
    type_map = {
        PredictionSeverity.CRITICAL: PredictionType.FAILURE,
        PredictionSeverity.HIGH: PredictionType.FAILURE,
        PredictionSeverity.MEDIUM: PredictionType.DEGRADATION,
        PredictionSeverity.LOW: PredictionType.CAPACITY,
    }
    
    return Prediction(
        id=uuid4(),
        api_id=api_id,
        prediction_type=type_map[severity],
        predicted_at=now,
        predicted_time=now + timedelta(hours=hours_ahead),
        confidence_score=confidence_map[severity],
        severity=severity,
        status=PredictionStatus.ACTIVE,
        contributing_factors=[
            ContributingFactor(
                factor=ContributingFactorType.INCREASING_ERROR_RATE,
                current_value=100.0,
                threshold=50.0,
                trend="increasing",
                weight=confidence_map[severity],
            )
        ],
        recommended_actions=["Test action"],
        actual_outcome=None,
        actual_time=None,
        accuracy_score=None,
        model_version="1.0.0",
        metadata={"test": True, "severity": severity.value},
    )


def create_metrics_series(
    api_id: UUID,
    gateway_id: UUID,
    hours: int = 24,
    degrading: bool = False
) -> List[Metric]:
    """
    Helper function to create a time series of metrics.
    
    Args:
        api_id: API ID for metrics
        gateway_id: Gateway ID for metrics
        hours: Number of hours of metrics to generate
        degrading: Whether metrics should show degradation
    
    Returns:
        List of Metric instances
    """
    now = datetime.utcnow()
    metrics = []
    
    for i in range(hours):
        timestamp = now - timedelta(hours=hours-1-i)
        
        if degrading:
            # Linear degradation
            progress = i / (hours - 1) if hours > 1 else 0
            error_rate = 0.02 + (0.13 * progress)  # 2% to 15%
            response_time_p95 = 100 + (300 * progress)  # 100ms to 400ms
            availability = 99.9 - (5.9 * progress)  # 99.9% to 94%
        else:
            # Stable metrics
            error_rate = 0.01
            response_time_p95 = 150.0
            availability = 99.9
        
        metric = Metric(
            id=uuid4(),
            api_id=api_id,
            gateway_id=gateway_id,
            timestamp=timestamp,
            response_time_p50=response_time_p95 * 0.6,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p95 * 1.2,
            error_rate=error_rate,
            error_count=int(error_rate * 1000),
            request_count=1000,
            throughput=16.67,
            availability=availability,
            status_codes={
                "200": int((1-error_rate) * 1000),
                "500": int(error_rate * 1000)
            },
            endpoint_metrics=None,
            metadata={"test": True, "degrading": degrading},
        )
        metrics.append(metric)
    
    return metrics


# Made with Bob