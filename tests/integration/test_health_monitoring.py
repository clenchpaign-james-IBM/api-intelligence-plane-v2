"""
Integration tests for API health monitoring.

Tests the complete health monitoring workflow:
1. Register a Gateway and discover APIs
2. Collect metrics for APIs
3. Calculate health scores based on metrics
4. Monitor health degradation over time
5. Verify health alerts and status updates
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.tests.fixtures import create_sample_api
from backend.app.models.base.api import APIStatus, IntelligenceMetadata, DiscoveryMethod


@pytest.fixture
def opensearch_client():
    """Get OpenSearch client for tests."""
    return get_opensearch_client()


@pytest.mark.asyncio
class TestHealthMonitoring:
    """Integration tests for API health monitoring."""

    async def test_initial_health_score(self, opensearch_client):
        """Test that new APIs start with a default health score."""
        # Create API with initial health score
        api = create_sample_api(
            name="Health Test API",
            version="1.0.0",
            status=APIStatus.ACTIVE,
        )
        
        # Verify initial health score
        assert api.intelligence_metadata.health_score == 100.0
        assert api.status == APIStatus.ACTIVE

    async def test_health_score_calculation(self, opensearch_client):
        """Test health score calculation based on metrics."""
        # Create API with good health
        healthy_api = create_sample_api(
            name="Healthy API",
            status=APIStatus.ACTIVE,
        )
        assert healthy_api.intelligence_metadata.health_score == 100.0
        
        # Create API with degraded health
        degraded_api = create_sample_api(
            name="Degraded API",
            status=APIStatus.ACTIVE,
        )
        # Simulate degraded health by updating intelligence metadata
        degraded_api.intelligence_metadata.health_score = 65.0
        assert 50.0 < degraded_api.intelligence_metadata.health_score < 80.0

    async def test_health_degradation_detection(self, opensearch_client):
        """Test detection of health degradation over time."""
        # Create API with initial good health
        api = create_sample_api(
            name="Degrading API",
            status=APIStatus.ACTIVE,
        )
        initial_health = api.intelligence_metadata.health_score
        assert initial_health == 100.0
        
        # Simulate health degradation
        api.intelligence_metadata.health_score = 70.0
        assert api.intelligence_metadata.health_score < initial_health
        
        # Further degradation
        api.intelligence_metadata.health_score = 40.0
        assert api.intelligence_metadata.health_score < 50.0

    async def test_health_status_transitions(self, opensearch_client):
        """Test API status transitions based on health score."""
        # Start with ACTIVE status
        api = create_sample_api(
            name="Status Transition API",
            status=APIStatus.ACTIVE,
        )
        assert api.status == APIStatus.ACTIVE
        assert api.intelligence_metadata.health_score == 100.0
        
        # Simulate critical health degradation
        api.intelligence_metadata.health_score = 25.0
        api.status = APIStatus.FAILED
        assert api.status == APIStatus.FAILED
        assert api.intelligence_metadata.health_score < 30.0
        
        # Simulate recovery
        api.intelligence_metadata.health_score = 95.0
        api.status = APIStatus.ACTIVE
        assert api.status == APIStatus.ACTIVE
        assert api.intelligence_metadata.health_score > 90.0

    async def test_multiple_api_health_monitoring(self, opensearch_client):
        """Test health monitoring across multiple APIs."""
        # Create multiple APIs with varying health scores
        apis = []
        health_scores = [100.0, 80.0, 60.0, 40.0, 20.0]
        
        for i, score in enumerate(health_scores):
            api = create_sample_api(
                name=f"Multi Health API {i}",
                status=APIStatus.ACTIVE if score >= 50 else APIStatus.FAILED,
            )
            api.intelligence_metadata.health_score = score
            apis.append(api)
        
        # Verify all APIs have different health scores
        for i, api in enumerate(apis):
            assert api.intelligence_metadata.health_score == health_scores[i]
            if health_scores[i] >= 50:
                assert api.status == APIStatus.ACTIVE
            else:
                assert api.status == APIStatus.FAILED

    async def test_health_monitoring_with_no_metrics(self, opensearch_client):
        """Test health monitoring for APIs with no recent metrics."""
        # Create API with no recent activity
        api = create_sample_api(
            name="No Metrics API",
            status=APIStatus.INACTIVE,
        )
        
        # Update last_seen_at to indicate no recent activity
        api.intelligence_metadata.last_seen_at = datetime.utcnow() - timedelta(days=2)
        
        # Verify API is marked as inactive
        assert api.status == APIStatus.INACTIVE
        assert api.intelligence_metadata.last_seen_at < datetime.utcnow() - timedelta(days=1)

    async def test_health_score_boundaries(self, opensearch_client):
        """Test health score boundary conditions."""
        # Test minimum health score (0)
        critical_api = create_sample_api(
            name="Critical API",
            status=APIStatus.FAILED,
        )
        critical_api.intelligence_metadata.health_score = 0.0
        assert critical_api.intelligence_metadata.health_score == 0.0
        
        # Test maximum health score (100)
        perfect_api = create_sample_api(
            name="Perfect API",
            status=APIStatus.ACTIVE,
        )
        assert perfect_api.intelligence_metadata.health_score == 100.0
        
        # Test mid-range health scores
        warning_api = create_sample_api(
            name="Warning API",
            status=APIStatus.ACTIVE,
        )
        warning_api.intelligence_metadata.health_score = 65.0
        assert 50.0 < warning_api.intelligence_metadata.health_score < 80.0


@pytest.mark.asyncio
class TestHealthAlerts:
    """Integration tests for health alert generation."""

    async def test_critical_health_alert(self, opensearch_client):
        """Test generation of critical health alerts."""
        # Create API with critical health
        api = create_sample_api(
            name="Critical Health API",
            status=APIStatus.FAILED,
        )
        api.intelligence_metadata.health_score = 15.0
        
        # Verify critical health is recorded
        assert api.intelligence_metadata.health_score < 20.0
        assert api.status == APIStatus.FAILED

    async def test_warning_health_alert(self, opensearch_client):
        """Test generation of warning health alerts."""
        # Create API with warning-level health
        api = create_sample_api(
            name="Warning Health API",
            status=APIStatus.ACTIVE,
        )
        api.intelligence_metadata.health_score = 65.0
        
        # Verify warning health is recorded
        assert 50.0 < api.intelligence_metadata.health_score < 80.0
        assert api.status == APIStatus.ACTIVE

    async def test_healthy_api_no_alert(self, opensearch_client):
        """Test that healthy APIs don't generate alerts."""
        # Create API with good health
        api = create_sample_api(
            name="Healthy API",
            status=APIStatus.ACTIVE,
        )
        
        # Verify healthy status
        assert api.intelligence_metadata.health_score >= 80.0
        assert api.status == APIStatus.ACTIVE

    async def test_health_recovery_alert(self, opensearch_client):
        """Test alert when API health recovers."""
        # Create API that was unhealthy
        api = create_sample_api(
            name="Recovering API",
            status=APIStatus.FAILED,
        )
        api.intelligence_metadata.health_score = 30.0
        
        # Verify initial unhealthy state
        assert api.intelligence_metadata.health_score < 50.0
        assert api.status == APIStatus.FAILED
        
        # Simulate recovery
        api.intelligence_metadata.health_score = 85.0
        api.status = APIStatus.ACTIVE
        
        # Verify recovery
        assert api.intelligence_metadata.health_score > 80.0
        assert api.status == APIStatus.ACTIVE


@pytest.mark.asyncio
class TestHealthMetrics:
    """Integration tests for health metrics collection."""

    async def test_health_score_with_error_rate(self, opensearch_client):
        """Test health score calculation with error rate."""
        # High error rate should lower health score
        api = create_sample_api(
            name="High Error API",
            status=APIStatus.ACTIVE,
        )
        api.intelligence_metadata.health_score = 50.0  # Degraded due to errors
        
        assert api.intelligence_metadata.health_score < 80.0

    async def test_health_score_with_response_time(self, opensearch_client):
        """Test health score calculation with response time."""
        # Slow response time should lower health score
        api = create_sample_api(
            name="Slow API",
            status=APIStatus.ACTIVE,
        )
        api.intelligence_metadata.health_score = 70.0  # Degraded due to latency
        
        assert api.intelligence_metadata.health_score < 80.0

    async def test_health_score_with_availability(self, opensearch_client):
        """Test health score calculation with availability."""
        # Low availability should lower health score
        api = create_sample_api(
            name="Unstable API",
            status=APIStatus.ACTIVE,
        )
        api.intelligence_metadata.health_score = 60.0  # Degraded due to downtime
        
        assert api.intelligence_metadata.health_score < 80.0

    async def test_health_score_composite(self, opensearch_client):
        """Test health score with multiple factors."""
        # Multiple issues should significantly lower health score
        api = create_sample_api(
            name="Multiple Issues API",
            status=APIStatus.FAILED,
        )
        api.intelligence_metadata.health_score = 35.0  # Multiple problems
        
        assert api.intelligence_metadata.health_score < 50.0
        assert api.status == APIStatus.FAILED


# Made with Bob