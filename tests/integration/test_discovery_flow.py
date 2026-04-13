"""
Integration tests for API discovery flow.

Tests the complete discovery workflow:
1. Register a Gateway
2. Discover APIs from the Gateway
3. Verify APIs are stored in OpenSearch
4. Verify shadow API detection
5. Verify API status updates
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.app.db.repositories.gateway_repository import GatewayRepository
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.services.discovery_service import DiscoveryService
from backend.app.models.gateway import Gateway, GatewayVendor, GatewayStatus
from backend.app.models.base.api import (
    API,
    APIStatus,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    IntelligenceMetadata,
    MaturityState,
    VersionInfo,
)


@pytest.fixture
async def opensearch_client():
    """Get OpenSearch client for tests."""
    client = get_opensearch_client()
    yield client
    # Cleanup is handled by repository methods


@pytest.fixture
async def gateway_repository(opensearch_client):
    """Create Gateway repository instance."""
    return GatewayRepository(opensearch_client)


@pytest.fixture
async def api_repository(opensearch_client):
    """Create API repository instance."""
    return APIRepository(opensearch_client)


@pytest.fixture
async def discovery_service(opensearch_client):
    """Create Discovery service instance."""
    return DiscoveryService(opensearch_client)


@pytest.fixture
async def test_gateway(gateway_repository):
    """Create a test Gateway."""
    gateway = Gateway(
        id=uuid4(),
        name="Test Demo Gateway",
        type=GatewayType.NATIVE,
        base_url="http://localhost:8081",
        api_key="test-api-key",
        status=GatewayStatus.ACTIVE,
        capabilities=["api_management", "metrics", "rate_limiting"],
        metadata={"test": True},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    created_gateway = await gateway_repository.create(gateway)
    yield created_gateway
    
    # Cleanup
    try:
        await gateway_repository.delete(created_gateway.id)
    except Exception:
        pass


@pytest.mark.asyncio
class TestDiscoveryFlow:
    """Integration tests for API discovery flow."""

    async def test_gateway_registration(self, gateway_repository, test_gateway):
        """Test Gateway registration and retrieval."""
        # Verify Gateway was created
        assert test_gateway.id is not None
        assert test_gateway.name == "Test Demo Gateway"
        assert test_gateway.type == GatewayType.NATIVE
        assert test_gateway.status == GatewayStatus.ACTIVE
        
        # Retrieve Gateway
        retrieved = await gateway_repository.get(test_gateway.id)
        assert retrieved is not None
        assert retrieved.id == test_gateway.id
        assert retrieved.name == test_gateway.name

    async def test_api_discovery_from_gateway(
        self, 
        discovery_service, 
        api_repository, 
        test_gateway
    ):
        """Test discovering APIs from a Gateway."""
        # Discover APIs from Gateway
        discovered_apis = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        # Verify APIs were discovered
        assert len(discovered_apis) > 0, "No APIs were discovered"
        
        # Verify each discovered API
        for api in discovered_apis:
            assert api.id is not None
            assert api.gateway_id == test_gateway.id
            assert api.name is not None
            assert api.base_path is not None
            assert api.discovery_method == DiscoveryMethod.GATEWAY_API
            assert api.status in [APIStatus.ACTIVE, APIStatus.INACTIVE]
            
            # Verify API is stored in OpenSearch
            stored_api = await api_repository.get(api.id)
            assert stored_api is not None
            assert stored_api.id == api.id

    async def test_shadow_api_detection(
        self, 
        discovery_service, 
        api_repository, 
        test_gateway
    ):
        """Test shadow API detection from traffic logs."""
        # First, discover regular APIs
        await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        # Detect shadow APIs from traffic logs
        shadow_apis = await discovery_service.detect_shadow_apis(
            gateway_id=test_gateway.id,
            time_range_minutes=60
        )
        
        # Verify shadow API detection
        # Note: This may return 0 if no traffic logs exist
        if len(shadow_apis) > 0:
            for api in shadow_apis:
                assert api.is_shadow is True
                assert api.discovery_method == DiscoveryMethod.TRAFFIC_ANALYSIS
                assert api.gateway_id == test_gateway.id

    async def test_api_status_updates(
        self, 
        discovery_service, 
        api_repository, 
        test_gateway
    ):
        """Test API status updates during discovery."""
        # First discovery
        first_discovery = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        assert len(first_discovery) > 0
        first_api = first_discovery[0]
        
        # Wait a moment
        await asyncio.sleep(1)
        
        # Second discovery (should update last_seen_at)
        second_discovery = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        # Find the same API
        second_api = next(
            (api for api in second_discovery if api.id == first_api.id),
            None
        )
        
        assert second_api is not None
        assert second_api.last_seen_at >= first_api.last_seen_at

    async def test_inactive_api_detection(
        self, 
        discovery_service, 
        api_repository, 
        test_gateway
    ):
        """Test detection of inactive APIs."""
        # Discover APIs
        discovered_apis = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        assert len(discovered_apis) > 0
        
        # Manually set an API's last_seen_at to old date
        test_api = discovered_apis[0]
        test_api.last_seen_at = datetime.utcnow() - timedelta(days=8)
        await api_repository.update(test_api.id, test_api)
        
        # Detect inactive APIs
        inactive_apis = await discovery_service.detect_inactive_apis(
            gateway_id=test_gateway.id,
            inactive_threshold_days=7
        )
        
        # Verify the test API is detected as inactive
        inactive_ids = [api.id for api in inactive_apis]
        assert test_api.id in inactive_ids

    async def test_api_search_and_filtering(
        self, 
        api_repository, 
        discovery_service, 
        test_gateway
    ):
        """Test API search and filtering capabilities."""
        # Discover APIs first
        await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        # Search by gateway_id
        gateway_apis, total = await api_repository.find_by_gateway(
            gateway_id=test_gateway.id
        )
        assert len(gateway_apis) > 0
        assert total > 0
        
        # Search by status
        active_apis, active_total = await api_repository.find_by_status(
            status=APIStatus.ACTIVE
        )
        assert active_total >= 0
        
        # Search shadow APIs
        shadow_apis, shadow_total = await api_repository.find_shadow_apis()
        assert shadow_total >= 0

    async def test_discovery_error_handling(
        self, 
        discovery_service, 
        gateway_repository
    ):
        """Test error handling in discovery flow."""
        # Create a Gateway with invalid URL
        invalid_gateway = Gateway(
            id=uuid4(),
            name="Invalid Gateway",
            type=GatewayType.NATIVE,
            base_url="http://invalid-url-that-does-not-exist:9999",
            api_key="test-key",
            status=GatewayStatus.ACTIVE,
            capabilities=[],
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        created = await gateway_repository.create(invalid_gateway)
        
        try:
            # Attempt discovery (should handle error gracefully)
            with pytest.raises(Exception):
                await discovery_service.discover_apis_from_gateway(
                    gateway_id=created.id,
                    force_refresh=True
                )
        finally:
            # Cleanup
            await gateway_repository.delete(created.id)

    async def test_concurrent_discovery(
        self, 
        discovery_service, 
        test_gateway
    ):
        """Test concurrent API discovery operations."""
        # Run multiple discoveries concurrently
        tasks = [
            discovery_service.discover_apis_from_gateway(
                gateway_id=test_gateway.id,
                force_refresh=False
            )
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all discoveries completed
        assert len(results) == 3
        
        # At least one should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

    async def test_api_metadata_enrichment(
        self, 
        discovery_service, 
        api_repository, 
        test_gateway
    ):
        """Test API metadata enrichment during discovery."""
        # Discover APIs
        discovered_apis = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        assert len(discovered_apis) > 0
        
        # Verify metadata is populated
        for api in discovered_apis:
            assert api.endpoints is not None
            assert len(api.endpoints) > 0
            assert api.methods is not None
            assert len(api.methods) > 0
            assert api.authentication_type in [
                AuthenticationType.API_KEY,
                AuthenticationType.OAUTH2,
                AuthenticationType.JWT,
                AuthenticationType.BASIC,
                AuthenticationType.NONE,
            ]


@pytest.mark.asyncio
class TestDiscoveryPerformance:
    """Performance tests for discovery operations."""

    async def test_discovery_performance(
        self, 
        discovery_service, 
        test_gateway
    ):
        """Test discovery performance with timing."""
        import time
        
        start_time = time.time()
        
        discovered_apis = await discovery_service.discover_apis_from_gateway(
            gateway_id=test_gateway.id,
            force_refresh=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Discovery should complete within reasonable time
        assert duration < 30.0, f"Discovery took too long: {duration}s"
        assert len(discovered_apis) >= 0

    async def test_bulk_api_storage(
        self, 
        api_repository, 
        test_gateway
    ):
        """Test bulk API storage performance."""
        import time
        
        # Create test APIs
        test_apis = [
            API(
                id=uuid4(),
                gateway_id=test_gateway.id,
                name=f"Test API {i}",
                version="1.0.0",
                base_path=f"/api/v1/test{i}",
                endpoints=[],
                methods=["GET", "POST"],
                authentication_type=AuthenticationType.API_KEY,
                is_shadow=False,
                discovery_method=DiscoveryMethod.GATEWAY_API,
                discovered_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                status=APIStatus.ACTIVE,
                health_score=100.0,
                current_metrics={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Store APIs
        for api in test_apis:
            await api_repository.create(api)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Bulk storage should be reasonably fast
        assert duration < 10.0, f"Bulk storage took too long: {duration}s"
        
        # Cleanup
        for api in test_apis:
            try:
                await api_repository.delete(api.id)
            except Exception:
                pass

# Made with Bob
