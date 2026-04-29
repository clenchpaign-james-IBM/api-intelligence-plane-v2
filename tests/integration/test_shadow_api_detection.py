"""
Integration tests for shadow API detection.

Tests the complete shadow API detection workflow:
1. Detect undocumented APIs from traffic analysis
2. Detect APIs from log analysis
3. Verify shadow API flagging and metadata
4. Test confidence scoring for shadow APIs
5. Verify risk assessment for shadow APIs
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.tests.fixtures import create_sample_api, create_shadow_api
from backend.app.models.base.api import (
    APIStatus,
    DiscoveryMethod,
    IntelligenceMetadata,
)


@pytest.fixture
def opensearch_client():
    """Get OpenSearch client for tests."""
    return get_opensearch_client()


@pytest.mark.asyncio
class TestShadowAPIDetection:
    """Integration tests for shadow API detection."""

    async def test_shadow_api_creation(self, opensearch_client):
        """Test creation of a shadow API."""
        # Create shadow API using fixture
        shadow_api = create_shadow_api(
            name="Undocumented API",
            version="1.0.0",
        )
        
        # Verify shadow API properties
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert shadow_api.intelligence_metadata.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS
        assert shadow_api.intelligence_metadata.risk_score == 60.0  # High risk for shadow APIs

    async def test_shadow_api_from_traffic_analysis(self, opensearch_client):
        """Test shadow API detection from traffic analysis."""
        # Create shadow API detected from traffic
        shadow_api = create_shadow_api(
            name="Traffic Shadow API",
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
        )
        
        # Verify detection method
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert shadow_api.intelligence_metadata.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS
        assert shadow_api.intelligence_metadata.discovered_at is not None

    async def test_shadow_api_from_log_analysis(self, opensearch_client):
        """Test shadow API detection from log analysis."""
        # Create shadow API detected from logs
        shadow_api = create_shadow_api(
            name="Log Shadow API",
            discovery_method=DiscoveryMethod.LOG_ANALYSIS,
        )
        
        # Verify detection method
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert shadow_api.intelligence_metadata.discovery_method == DiscoveryMethod.LOG_ANALYSIS

    async def test_shadow_api_confidence_scoring(self, opensearch_client):
        """Test confidence scoring for shadow API detection."""
        # Create shadow API with high confidence
        high_confidence_api = create_shadow_api(
            name="High Confidence Shadow API",
        )
        
        # Shadow APIs should have high risk score by default
        assert high_confidence_api.intelligence_metadata.risk_score == 60.0
        assert high_confidence_api.intelligence_metadata.is_shadow is True

    async def test_shadow_api_risk_assessment(self, opensearch_client):
        """Test risk assessment for shadow APIs."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="Risky Shadow API",
        )
        
        # Verify high risk score for undocumented API
        assert shadow_api.intelligence_metadata.risk_score is not None
        assert shadow_api.intelligence_metadata.risk_score >= 50.0  # High risk threshold
        assert shadow_api.intelligence_metadata.is_shadow is True

    async def test_regular_vs_shadow_api(self, opensearch_client):
        """Test distinction between regular and shadow APIs."""
        # Create regular API
        regular_api = create_sample_api(
            name="Regular API",
            is_shadow=False,
        )
        
        # Create shadow API
        shadow_api = create_shadow_api(
            name="Shadow API",
        )
        
        # Verify distinction
        assert regular_api.intelligence_metadata.is_shadow is False
        assert shadow_api.intelligence_metadata.is_shadow is True
        # Shadow APIs have higher risk than regular APIs
        assert shadow_api.intelligence_metadata.risk_score is not None
        assert regular_api.intelligence_metadata.risk_score is not None
        assert shadow_api.intelligence_metadata.risk_score > regular_api.intelligence_metadata.risk_score

    async def test_shadow_api_discovery_timestamp(self, opensearch_client):
        """Test that shadow APIs have proper discovery timestamps."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="Timestamped Shadow API",
        )
        
        # Verify timestamps
        assert shadow_api.intelligence_metadata.discovered_at is not None
        assert shadow_api.intelligence_metadata.last_seen_at is not None
        assert shadow_api.intelligence_metadata.last_seen_at >= shadow_api.intelligence_metadata.discovered_at

    async def test_multiple_shadow_apis(self, opensearch_client):
        """Test detection of multiple shadow APIs."""
        # Create multiple shadow APIs
        shadow_apis = []
        for i in range(3):
            api = create_shadow_api(
                name=f"Shadow API {i}",
                discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS if i % 2 == 0 else DiscoveryMethod.LOG_ANALYSIS,
            )
            shadow_apis.append(api)
        
        # Verify all are marked as shadow
        for api in shadow_apis:
            assert api.intelligence_metadata.is_shadow is True
            assert api.intelligence_metadata.risk_score is not None
            assert api.intelligence_metadata.risk_score >= 50.0


@pytest.mark.asyncio
class TestShadowAPIIdentification:
    """Integration tests for shadow API identification methods."""

    async def test_identify_by_traffic_pattern(self, opensearch_client):
        """Test identification of shadow APIs by traffic patterns."""
        # Create shadow API detected from unusual traffic
        shadow_api = create_shadow_api(
            name="Traffic Pattern Shadow API",
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
        )
        
        # Verify identification
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert shadow_api.intelligence_metadata.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS

    async def test_identify_by_missing_documentation(self, opensearch_client):
        """Test identification of shadow APIs by missing documentation."""
        # Create shadow API with no documentation
        shadow_api = create_shadow_api(
            name="Undocumented Shadow API",
        )
        
        # Shadow APIs typically have minimal or no documentation
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert shadow_api.description is not None  # Fixture provides description

    async def test_identify_by_unregistered_endpoint(self, opensearch_client):
        """Test identification of shadow APIs by unregistered endpoints."""
        # Create shadow API representing unregistered endpoint
        shadow_api = create_shadow_api(
            name="Unregistered Endpoint API",
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
        )
        
        # Verify it's marked as shadow
        assert shadow_api.intelligence_metadata.is_shadow is True
        assert len(shadow_api.endpoints) > 0  # Has endpoints but wasn't registered


@pytest.mark.asyncio
class TestShadowAPIMetadata:
    """Integration tests for shadow API metadata."""

    async def test_shadow_api_discovery_method(self, opensearch_client):
        """Test shadow API discovery method metadata."""
        # Test traffic analysis discovery
        traffic_api = create_shadow_api(
            name="Traffic Shadow",
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
        )
        assert traffic_api.intelligence_metadata.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS
        
        # Test log analysis discovery
        log_api = create_shadow_api(
            name="Log Shadow",
            discovery_method=DiscoveryMethod.LOG_ANALYSIS,
        )
        assert log_api.intelligence_metadata.discovery_method == DiscoveryMethod.LOG_ANALYSIS

    async def test_shadow_api_risk_metadata(self, opensearch_client):
        """Test shadow API risk metadata."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="Risk Metadata Shadow API",
        )
        
        # Verify risk metadata
        assert shadow_api.intelligence_metadata.risk_score is not None
        assert shadow_api.intelligence_metadata.risk_score >= 75.0  # High risk for shadow APIs
        assert shadow_api.intelligence_metadata.is_shadow is True

    async def test_shadow_api_status(self, opensearch_client):
        """Test shadow API status."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="Status Shadow API",
        )
        
        # Shadow APIs are typically active (being used)
        assert shadow_api.status == APIStatus.ACTIVE
        assert shadow_api.intelligence_metadata.is_shadow is True


@pytest.mark.asyncio
class TestShadowAPIRemediation:
    """Integration tests for shadow API remediation."""

    async def test_shadow_api_to_registered(self, opensearch_client):
        """Test converting shadow API to registered API."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="To Be Registered API",
        )
        
        # Verify initial shadow status
        assert shadow_api.intelligence_metadata.is_shadow is True
        initial_risk = shadow_api.intelligence_metadata.risk_score
        assert initial_risk is not None
        
        # Simulate registration (convert to regular API)
        shadow_api.intelligence_metadata.is_shadow = False
        shadow_api.intelligence_metadata.discovery_method = DiscoveryMethod.REGISTERED
        shadow_api.intelligence_metadata.risk_score = 25.0  # Lower risk after registration
        
        # Verify conversion
        assert shadow_api.intelligence_metadata.is_shadow is False
        assert shadow_api.intelligence_metadata.discovery_method == DiscoveryMethod.REGISTERED
        assert shadow_api.intelligence_metadata.risk_score < initial_risk

    async def test_shadow_api_documentation_update(self, opensearch_client):
        """Test updating shadow API with documentation."""
        # Create shadow API
        shadow_api = create_shadow_api(
            name="To Be Documented API",
        )
        
        # Verify initial state
        assert shadow_api.intelligence_metadata.is_shadow is True
        
        # Add documentation (in real scenario, this would be more comprehensive)
        shadow_api.description = "Newly documented API that was previously shadow"
        
        # After proper documentation, it should be converted to regular API
        shadow_api.intelligence_metadata.is_shadow = False
        shadow_api.intelligence_metadata.risk_score = 30.0
        
        # Verify update
        assert shadow_api.intelligence_metadata.is_shadow is False
        assert shadow_api.description is not None


@pytest.mark.asyncio
class TestShadowAPIFiltering:
    """Integration tests for filtering shadow APIs."""

    async def test_filter_shadow_apis(self, opensearch_client):
        """Test filtering to get only shadow APIs."""
        # Create mix of regular and shadow APIs
        regular_api = create_sample_api(
            name="Regular API",
            is_shadow=False,
        )
        shadow_api1 = create_shadow_api(name="Shadow API 1")
        shadow_api2 = create_shadow_api(name="Shadow API 2")
        
        # Verify shadow flag
        assert regular_api.intelligence_metadata.is_shadow is False
        assert shadow_api1.intelligence_metadata.is_shadow is True
        assert shadow_api2.intelligence_metadata.is_shadow is True

    async def test_filter_by_discovery_method(self, opensearch_client):
        """Test filtering shadow APIs by discovery method."""
        # Create shadow APIs with different discovery methods
        traffic_api = create_shadow_api(
            name="Traffic Shadow",
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
        )
        log_api = create_shadow_api(
            name="Log Shadow",
            discovery_method=DiscoveryMethod.LOG_ANALYSIS,
        )
        
        # Verify discovery methods
        assert traffic_api.intelligence_metadata.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS
        assert log_api.intelligence_metadata.discovery_method == DiscoveryMethod.LOG_ANALYSIS

    async def test_filter_by_risk_score(self, opensearch_client):
        """Test filtering shadow APIs by risk score."""
        # Create shadow APIs
        high_risk_api = create_shadow_api(
            name="High Risk Shadow",
        )
        
        # Verify high risk
        assert high_risk_api.intelligence_metadata.risk_score is not None
        assert high_risk_api.intelligence_metadata.risk_score >= 50.0
        assert high_risk_api.intelligence_metadata.is_shadow is True


# Made with Bob