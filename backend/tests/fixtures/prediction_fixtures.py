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
from app.models.base.metric import Metric, TimeBucket
from app.models.base.api import (
    API,
    APIStatus,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    IntelligenceMetadata,
    MaturityState,
    VersionInfo,
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
        api_name="Test API",
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
        api_name="Critical API",
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
        api_name="Resolved API",
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
    """Generate a sample stable metric with time-bucketed structure."""
    now = datetime.utcnow()
    return Metric(
        id=uuid4(),
        api_id=str(sample_api_id),
        gateway_id=sample_gateway_id,
        application_id=None,
        operation=None,
        timestamp=now,
        time_bucket=TimeBucket.ONE_HOUR,
        request_count=1000,
        success_count=990,
        failure_count=10,
        timeout_count=0,
        error_rate=1.0,
        availability=99.0,
        response_time_avg=100.0,
        response_time_min=50.0,
        response_time_max=300.0,
        response_time_p50=80.0,
        response_time_p95=150.0,
        response_time_p99=200.0,
        gateway_time_avg=20.0,
        backend_time_avg=80.0,
        throughput=0.278,  # 1000 requests / 3600 seconds
        total_data_size=2048000,  # ~2MB
        avg_request_size=512.0,
        avg_response_size=1536.0,
        cache_hit_count=0,
        cache_miss_count=0,
        cache_bypass_count=0,
        cache_hit_rate=0.0,
        status_2xx_count=990,
        status_3xx_count=0,
        status_4xx_count=0,
        status_5xx_count=10,
        status_codes={"200": 990, "500": 10},
        endpoint_metrics=None,
        vendor_metadata={"test": True},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_degrading_metric(sample_api_id, sample_gateway_id) -> Metric:
    """Generate a sample degrading metric with time-bucketed structure."""
    now = datetime.utcnow()
    return Metric(
        id=uuid4(),
        api_id=str(sample_api_id),
        gateway_id=sample_gateway_id,
        application_id=None,
        operation=None,
        timestamp=now,
        time_bucket=TimeBucket.ONE_HOUR,
        request_count=1000,
        success_count=850,
        failure_count=150,
        timeout_count=0,
        error_rate=15.0,
        availability=85.0,
        response_time_avg=350.0,
        response_time_min=100.0,
        response_time_max=800.0,
        response_time_p50=200.0,
        response_time_p95=400.0,
        response_time_p99=600.0,
        gateway_time_avg=50.0,
        backend_time_avg=300.0,
        throughput=0.278,  # 1000 requests / 3600 seconds
        total_data_size=2048000,  # ~2MB
        avg_request_size=512.0,
        avg_response_size=1536.0,
        cache_hit_count=0,
        cache_miss_count=0,
        cache_bypass_count=0,
        cache_hit_rate=0.0,
        status_2xx_count=850,
        status_3xx_count=0,
        status_4xx_count=0,
        status_5xx_count=150,
        status_codes={"200": 850, "500": 150},
        endpoint_metrics=None,
        vendor_metadata={"test": True, "degrading": True},
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_test_api(sample_api_id, sample_gateway_id) -> API:
    """Generate a sample test API with vendor-neutral structure."""
    now = datetime.utcnow()
    return API(
        id=sample_api_id,
        gateway_id=sample_gateway_id,
        name="Test API",
        display_name="Test API Display",
        description="Test API for predictions",
        base_path="/api/v1",
        version_info=VersionInfo(
            current_version="1.0.0",
            previous_version=None,
            next_version=None,
            system_version=1,
            version_history=None,
        ),
        type=APIType.REST,
        maturity_state=MaturityState.PRODUCTIVE,
        endpoints=[
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint",
                parameters=[],
                response_codes=[200, 500],
                connection_timeout=None,
                read_timeout=None,
            )
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.NONE,
        authentication_config=None,
        ownership=None,
        tags=["test"],
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=now,
            last_seen_at=now,
            health_score=95.0,
            risk_score=5.0,
            security_score=90.0,
            compliance_status=None,
            usage_trend="stable",
            has_active_predictions=False,
        ),
        status=APIStatus.ACTIVE,
        is_active=True,
        vendor_metadata={"test": True},
        created_at=now,
        updated_at=now,
    )


def create_prediction_with_severity(
    api_id: UUID,
    api_name: str = "Test API",
    severity: PredictionSeverity = PredictionSeverity.HIGH,
    hours_ahead: int = 36
) -> Prediction:
    """
    Helper function to create a prediction with specific severity.
    
    Args:
        api_id: API ID for the prediction
        api_name: API name
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
        api_name=api_name,
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
    Helper function to create a time series of metrics with time-bucketed structure.
    
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
            error_rate = 2.0 + (13.0 * progress)  # 2% to 15%
            response_time_p95 = 100 + (300 * progress)  # 100ms to 400ms
            availability = 99.9 - (5.9 * progress)  # 99.9% to 94%
        else:
            # Stable metrics
            error_rate = 1.0
            response_time_p95 = 150.0
            availability = 99.0
        
        failure_count = int((error_rate / 100) * 1000)
        success_count = 1000 - failure_count
        
        metric = Metric(
            id=uuid4(),
            api_id=str(api_id),
            gateway_id=gateway_id,
            application_id=None,
            operation=None,
            timestamp=timestamp,
            time_bucket=TimeBucket.ONE_HOUR,
            request_count=1000,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=0,
            error_rate=error_rate,
            availability=availability,
            response_time_avg=response_time_p95 * 0.7,
            response_time_min=50.0,
            response_time_max=response_time_p95 * 1.5,
            response_time_p50=response_time_p95 * 0.6,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p95 * 1.2,
            gateway_time_avg=20.0,
            backend_time_avg=response_time_p95 * 0.6,
            throughput=0.278,  # 1000 requests / 3600 seconds
            total_data_size=2048000,
            avg_request_size=512.0,
            avg_response_size=1536.0,
            cache_hit_count=0,
            cache_miss_count=0,
            cache_bypass_count=0,
            cache_hit_rate=0.0,
            status_2xx_count=success_count,
            status_3xx_count=0,
            status_4xx_count=0,
            status_5xx_count=failure_count,
            status_codes={
                "200": success_count,
                "500": failure_count
            },
            endpoint_metrics=None,
            vendor_metadata={"test": True, "degrading": degrading},
            created_at=timestamp,
            updated_at=timestamp,
        )
        metrics.append(metric)
    
    return metrics


# Made with Bob