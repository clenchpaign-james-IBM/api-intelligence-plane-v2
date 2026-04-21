"""Integration tests for rate limiting functionality.

Tests the rate limiting service with real OpenSearch data to verify:
- Policy creation and management
- Adaptive threshold adjustments
- Effectiveness tracking
- Policy suggestions based on traffic patterns
- Policy activation/deactivation

Requires OpenSearch to be running and accessible.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.client import get_client
from app.db.repositories.rate_limit_repository import RateLimitPolicyRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.rate_limit_service import RateLimitService
from app.models.rate_limit import (
    RateLimitPolicy,
    PolicyType,
    PolicyStatus,
    EnforcementAction,
    LimitThresholds,
    AdaptationParameters,
    PriorityRule,
)
from app.models.base.metric import Metric
from app.models.base.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)


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


@pytest.fixture(scope="module")
def policy_repository(opensearch_client):
    """Create rate limit policy repository."""
    return RateLimitPolicyRepository(opensearch_client)


@pytest.fixture(scope="module")
def metrics_repository(opensearch_client):
    """Create metrics repository."""
    return MetricsRepository(opensearch_client)


@pytest.fixture(scope="module")
def api_repository(opensearch_client):
    """Create API repository."""
    return APIRepository(opensearch_client)


@pytest.fixture(scope="module")
def rate_limit_service(policy_repository, metrics_repository):
    """Create rate limiting service."""
    return RateLimitService(policy_repository, metrics_repository)


@pytest.fixture
def sample_api(api_repository):
    """Create a sample API for testing."""
    api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="Test API",
        base_path="/api/test",
        endpoints=[
            Endpoint(
                path="/users",
                method="GET",
                description="Get users",
            )
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.BEARER,
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        status=APIStatus.ACTIVE,
        health_score=0.95,
        current_metrics=CurrentMetrics(
            response_time_p50=120.0,
            response_time_p95=250.0,
            response_time_p99=400.0,
            error_rate=0.01,
            throughput=100.0,
            availability=0.99,
            measured_at=datetime.utcnow(),
        ),
    )
    
    # Store API
    api_repository.create(api.model_dump(), str(api.id))
    
    yield api
    
    # Cleanup
    try:
        api_repository.delete(str(api.id))
    except:
        pass


@pytest.fixture
def sample_metrics(metrics_repository, sample_api):
    """Create sample metrics for testing."""
    metrics = []
    now = datetime.utcnow()
    
    # Create 24 hours of metrics with varying throughput
    for i in range(24):
        timestamp = now - timedelta(hours=23 - i)
        
        # Simulate traffic pattern: higher during business hours
        hour = timestamp.hour
        if 9 <= hour <= 17:
            throughput = 150.0 + (i % 3) * 20  # Business hours: 150-190 req/s
        else:
            throughput = 50.0 + (i % 3) * 10   # Off hours: 50-70 req/s
        
        metric = Metric(
            id=uuid4(),
            api_id=sample_api.id,
            gateway_id=sample_api.gateway_id,
            timestamp=timestamp,
            response_time_p50=100.0 + (i % 5) * 10,
            response_time_p95=200.0 + (i % 5) * 20,
            response_time_p99=350.0 + (i % 5) * 30,
            error_rate=0.01 + (i % 3) * 0.005,
            error_count=int(throughput * 0.01),
            request_count=int(throughput * 60),  # Convert to requests per minute
            throughput=throughput,
            availability=0.99,
            status_codes={"200": int(throughput * 59), "500": int(throughput * 0.6)},
        )
        
        metrics.append(metric)
        metrics_repository.create(metric.model_dump(), str(metric.id))
    
    yield metrics
    
    # Cleanup
    for metric in metrics:
        try:
            metrics_repository.delete(str(metric.id))
        except:
            pass


class TestRateLimitPolicyManagement:
    """Test rate limit policy creation and management."""
    
    def test_create_fixed_policy(self, rate_limit_service, sample_api):
        """Test creating a fixed rate limit policy."""
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Fixed Rate Limit",
            policy_type=PolicyType.FIXED,
            limit_thresholds=LimitThresholds(
                requests_per_second=100,
                requests_per_minute=5000,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
        )
        
        assert policy is not None
        assert policy.policy_name == "Fixed Rate Limit"
        assert policy.policy_type == PolicyType.FIXED
        assert policy.status == PolicyStatus.INACTIVE
        assert policy.limit_thresholds.requests_per_second == 100
        assert policy.enforcement_action == EnforcementAction.THROTTLE
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))
    
    def test_create_adaptive_policy(self, rate_limit_service, sample_api):
        """Test creating an adaptive rate limit policy."""
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Adaptive Rate Limit",
            policy_type=PolicyType.ADAPTIVE,
            limit_thresholds=LimitThresholds(
                requests_per_second=150,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
            adaptation_parameters=AdaptationParameters(
                learning_rate=0.1,
                adjustment_frequency=300,
                min_threshold=75,
                max_threshold=300,
            ),
        )
        
        assert policy is not None
        assert policy.policy_type == PolicyType.ADAPTIVE
        assert policy.adaptation_parameters is not None
        assert policy.adaptation_parameters.learning_rate == 0.1
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))


class TestPolicySuggestions:
    """Test intelligent policy suggestions based on traffic patterns."""
    
    def test_suggest_policy_for_api(self, rate_limit_service, sample_api, sample_metrics):
        """Test policy suggestion based on traffic analysis."""
        suggestion = rate_limit_service.suggest_policy_for_api(str(sample_api.id))
        
        assert suggestion is not None
        assert "suggested_policy" in suggestion
        assert "reasoning" in suggestion
        assert "traffic_analysis" in suggestion
        
        # Verify suggested policy has appropriate thresholds
        suggested_policy = suggestion["suggested_policy"]
        assert suggested_policy["policy_type"] in [pt.value for pt in PolicyType]
        assert "limit_thresholds" in suggested_policy
        
        # Verify traffic analysis
        traffic_analysis = suggestion["traffic_analysis"]
        assert traffic_analysis["avg_throughput"] > 0
        assert traffic_analysis["peak_throughput"] > traffic_analysis["avg_throughput"]


class TestAdaptiveAdjustment:
    """Test adaptive policy threshold adjustments."""
    
    def test_adjust_adaptive_policy(self, rate_limit_service, sample_api, sample_metrics):
        """Test adaptive policy adjustment based on utilization."""
        # Create adaptive policy
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Adaptive Test Policy",
            policy_type=PolicyType.ADAPTIVE,
            limit_thresholds=LimitThresholds(
                requests_per_second=100,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
            adaptation_parameters=AdaptationParameters(
                learning_rate=0.1,
                adjustment_frequency=300,
                min_threshold=50,
                max_threshold=200,
            ),
        )
        
        # Activate policy
        activated = rate_limit_service.activate_policy(str(policy.id))
        assert activated.status == PolicyStatus.ACTIVE
        
        # Adjust policy
        adjusted = rate_limit_service.adjust_adaptive_policy(str(policy.id))
        
        assert adjusted is not None
        # Thresholds should be adjusted based on traffic
        assert adjusted.limit_thresholds.requests_per_second != policy.limit_thresholds.requests_per_second
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))


class TestEffectivenessTracking:
    """Test policy effectiveness analysis."""
    
    def test_analyze_policy_effectiveness(self, rate_limit_service, sample_api, sample_metrics):
        """Test effectiveness analysis for a policy."""
        # Create and activate policy
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Test Effectiveness Policy",
            policy_type=PolicyType.FIXED,
            limit_thresholds=LimitThresholds(
                requests_per_second=150,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
        )
        
        activated = rate_limit_service.activate_policy(str(policy.id))
        
        # Analyze effectiveness
        analysis = rate_limit_service.analyze_policy_effectiveness(str(policy.id))
        
        assert analysis is not None
        assert "effectiveness_score" in analysis
        assert "metrics" in analysis
        assert "recommendations" in analysis
        
        # Verify effectiveness score is between 0 and 1
        assert 0 <= analysis["effectiveness_score"] <= 1
        
        # Verify metrics
        metrics = analysis["metrics"]
        assert "error_rate" in metrics
        assert "avg_response_time" in metrics
        assert "throttled_requests" in metrics
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))


class TestPolicyActivation:
    """Test policy activation and deactivation."""
    
    def test_activate_policy(self, rate_limit_service, sample_api):
        """Test activating a rate limit policy."""
        # Create policy
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Activation Test Policy",
            policy_type=PolicyType.FIXED,
            limit_thresholds=LimitThresholds(
                requests_per_second=100,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
        )
        
        assert policy.status == PolicyStatus.INACTIVE
        
        # Activate
        activated = rate_limit_service.activate_policy(str(policy.id))
        
        assert activated.status == PolicyStatus.ACTIVE
        assert activated.applied_at is not None
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))
    
    def test_deactivate_policy(self, rate_limit_service, sample_api):
        """Test deactivating a rate limit policy."""
        # Create and activate policy
        policy = rate_limit_service.create_policy(
            api_id=str(sample_api.id),
            policy_name="Deactivation Test Policy",
            policy_type=PolicyType.FIXED,
            limit_thresholds=LimitThresholds(
                requests_per_second=100,
            ),
            enforcement_action=EnforcementAction.THROTTLE,
        )
        
        activated = rate_limit_service.activate_policy(str(policy.id))
        assert activated.status == PolicyStatus.ACTIVE
        
        # Deactivate
        deactivated = rate_limit_service.deactivate_policy(str(policy.id))
        
        assert deactivated.status == PolicyStatus.INACTIVE
        
        # Cleanup
        rate_limit_service.policy_repository.delete(str(policy.id))


# Made with Bob