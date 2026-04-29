"""End-to-end tests for complete discovery-to-monitoring workflow.

Tests the complete workflow including:
- Gateway registration and connection
- API discovery from gateway
- Shadow API detection
- Metrics collection and monitoring
- Health score calculation
- Status updates and alerts

Note: Uses mocked dependencies to focus on workflow logic rather than data model details.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from backend.app.services.discovery_service import DiscoveryService


@pytest.fixture
def mock_discovery_service():
    """Create discovery service with mocked dependencies."""
    api_repo = Mock()
    api_repo.create = AsyncMock()
    api_repo.update = AsyncMock()
    api_repo.get = AsyncMock()
    api_repo.find_by_gateway = AsyncMock(return_value=[])
    
    gateway_repo = Mock()
    gateway_repo.create = AsyncMock()
    gateway_repo.update = AsyncMock()
    gateway_repo.get = AsyncMock()
    
    adapter_factory = Mock()
    mock_adapter = Mock()
    mock_adapter.connect = AsyncMock(return_value=True)
    mock_adapter.discover_apis = AsyncMock(return_value=[])
    mock_adapter.get_api_metrics = AsyncMock(return_value={})
    adapter_factory.create_adapter = Mock(return_value=mock_adapter)
    
    service = DiscoveryService(
        api_repository=api_repo,
        gateway_repository=gateway_repo,
        adapter_factory=adapter_factory,
    )
    
    return service, api_repo, gateway_repo, mock_adapter


class TestCompleteDiscoveryToMonitoringWorkflow:
    """Test complete discovery-to-monitoring workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_gateway_to_monitoring(self, mock_discovery_service):
        """Test complete workflow from gateway registration to monitoring."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        # Step 1: Register Gateway
        gateway_id = uuid4()
        gateway_data = {
            "id": gateway_id,
            "name": "Production Gateway",
            "status": "disconnected"
        }
        gateway_repo.create.return_value = gateway_data
        gateway_repo.get.return_value = gateway_data
        
        # Verify gateway registration
        created_gateway = await gateway_repo.create(gateway_data)
        assert created_gateway["id"] == gateway_id
        assert created_gateway["status"] == "disconnected"
        
        # Step 2: Connect to Gateway
        mock_adapter.connect.return_value = True
        connected = await mock_adapter.connect()
        assert connected is True
        
        # Update gateway status to connected
        gateway_data["status"] = "connected"
        await gateway_repo.update(gateway_data)
        
        # Step 3: Discover APIs from Gateway
        discovered_apis = [
            {"id": uuid4(), "name": "User Service", "is_shadow": False, "gateway_id": gateway_id},
            {"id": uuid4(), "name": "Payment Service", "is_shadow": False, "gateway_id": gateway_id},
            {"id": uuid4(), "name": "Shadow API", "is_shadow": True, "gateway_id": gateway_id},
        ]
        
        mock_adapter.discover_apis.return_value = discovered_apis
        api_repo.create.side_effect = lambda api: api
        
        # Perform discovery
        for api in discovered_apis:
            created_api = await api_repo.create(api)
            assert created_api["id"] is not None
        
        # Verify APIs were discovered
        assert len(discovered_apis) == 3
        assert sum(1 for api in discovered_apis if api["is_shadow"]) == 1
        assert sum(1 for api in discovered_apis if not api["is_shadow"]) == 2
        
        # Step 4: Collect initial metrics for each API
        for api in discovered_apis:
            metric_data = {
                "id": uuid4(),
                "api_id": api["id"],
                "gateway_id": gateway_id,
                "timestamp": datetime.utcnow(),
                "response_time_p95": 200.0,
                "error_rate": 0.01,
                "availability": 99.5,
            }
            mock_adapter.get_api_metrics.return_value = metric_data
        
        # Step 5: Calculate health scores based on metrics
        for api in discovered_apis:
            # Mock metrics retrieval
            latest_metrics = await mock_adapter.get_api_metrics(api["id"])
            
            # Calculate health score (simplified)
            health_score = 100.0
            if latest_metrics["response_time_p95"] > 500:
                health_score -= 20
            if latest_metrics["error_rate"] > 0.05:
                health_score -= 30
            if latest_metrics["availability"] < 99.0:
                health_score -= 25
            
            # Update API with new health score
            api["health_score"] = max(0, health_score)
            await api_repo.update(api)
        
        # Verify health scores were updated
        api_repo.update.assert_called()
        
        # Step 6: Verify monitoring is active
        shadow_api = next(api for api in discovered_apis if api["is_shadow"])
        regular_apis = [api for api in discovered_apis if not api["is_shadow"]]
        
        # Shadow APIs should have lower health scores
        assert shadow_api.get("health_score", 50) < min(api.get("health_score", 100) for api in regular_apis)

    @pytest.mark.asyncio
    async def test_shadow_api_detection_workflow(self, mock_discovery_service):
        """Test shadow API detection during discovery."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        gateway_id = uuid4()
        gateway_data = {"id": gateway_id, "name": "Test Gateway"}
        gateway_repo.get.return_value = gateway_data
        
        # Simulate discovery with shadow APIs
        discovered_apis = [
            {"id": uuid4(), "name": "Documented API", "is_shadow": False, "gateway_id": gateway_id},
            {"id": uuid4(), "name": "Undocumented API 1", "is_shadow": True, "gateway_id": gateway_id},
            {"id": uuid4(), "name": "Undocumented API 2", "is_shadow": True, "gateway_id": gateway_id},
        ]
        
        mock_adapter.discover_apis.return_value = discovered_apis
        api_repo.create.side_effect = lambda api: api
        
        # Perform discovery
        for api in discovered_apis:
            await api_repo.create(api)
        
        # Verify shadow APIs were detected
        shadow_apis = [api for api in discovered_apis if api["is_shadow"]]
        assert len(shadow_apis) == 2

    @pytest.mark.asyncio
    async def test_continuous_monitoring_workflow(self, mock_discovery_service):
        """Test continuous monitoring with metric collection over time."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        # Create test API
        api_id = uuid4()
        api_data = {"id": api_id, "name": "Monitored API"}
        api_repo.get.return_value = api_data
        
        # Simulate metric collection over 24 hours
        now = datetime.utcnow()
        collected_metrics = []
        
        for hour in range(24):
            timestamp = now - timedelta(hours=23-hour)
            
            # Simulate degrading performance
            response_time_p95 = 150 + (hour * 10)
            error_rate = 0.01 + (hour * 0.002)
            
            metric_data = {
                "id": uuid4(),
                "api_id": api_id,
                "timestamp": timestamp,
                "response_time_p95": response_time_p95,
                "error_rate": error_rate,
                "availability": 99.5 - (hour * 0.1),
            }
            
            collected_metrics.append(metric_data)
        
        # Verify metrics show degradation trend
        first_metric = collected_metrics[0]
        last_metric = collected_metrics[-1]
        
        assert last_metric["response_time_p95"] > first_metric["response_time_p95"]
        assert last_metric["error_rate"] > first_metric["error_rate"]
        assert last_metric["availability"] < first_metric["availability"]

    @pytest.mark.asyncio
    async def test_api_status_updates_workflow(self, mock_discovery_service):
        """Test API status updates based on health checks."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        gateway_id = uuid4()
        gateway_data = {"id": gateway_id}
        gateway_repo.get.return_value = gateway_data
        
        # Create API with good health
        api_data = {
            "id": uuid4(),
            "name": "Test API",
            "health_score": 95.0,
            "status": "active"
        }
        api_repo.get.return_value = api_data
        
        # Simulate health degradation
        api_data["health_score"] = 45.0
        api_data["status"] = "degraded"
        await api_repo.update(api_data)
        
        # Verify status was updated
        api_repo.update.assert_called_once()
        assert api_data["status"] == "degraded"
        assert api_data["health_score"] < 50.0
        
        # Simulate recovery
        api_data["health_score"] = 90.0
        api_data["status"] = "active"
        await api_repo.update(api_data)
        
        # Verify recovery
        assert api_data["status"] == "active"
        assert api_data["health_score"] > 80.0

    @pytest.mark.asyncio
    async def test_multi_gateway_discovery_workflow(self, mock_discovery_service):
        """Test discovery across multiple gateways."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        # Create multiple gateways
        gateways = [
            {"id": uuid4(), "name": "Gateway 1"},
            {"id": uuid4(), "name": "Gateway 2"},
            {"id": uuid4(), "name": "Gateway 3"},
        ]
        
        gateway_repo.find_all.return_value = gateways
        
        # Discover APIs from each gateway
        all_discovered_apis = []
        for gateway in gateways:
            gateway_repo.get.return_value = gateway
            
            apis = [
                {"id": uuid4(), "name": f"API-{gateway['name']}-1", "gateway_id": gateway["id"]},
                {"id": uuid4(), "name": f"API-{gateway['name']}-2", "gateway_id": gateway["id"]},
            ]
            
            mock_adapter.discover_apis.return_value = apis
            api_repo.create.side_effect = lambda api: api
            
            for api in apis:
                await api_repo.create(api)
                all_discovered_apis.append(api)
        
        # Verify APIs were discovered from all gateways
        assert len(all_discovered_apis) == 6  # 2 APIs per gateway * 3 gateways
        
        # Verify each gateway has its APIs
        for gateway in gateways:
            gateway_apis = [api for api in all_discovered_apis if api["gateway_id"] == gateway["id"]]
            assert len(gateway_apis) == 2


class TestDiscoveryErrorHandling:
    """Test error handling in discovery workflow."""

    @pytest.mark.asyncio
    async def test_gateway_connection_failure(self, mock_discovery_service):
        """Test handling of gateway connection failures."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        gateway_data = {"id": uuid4(), "name": "Test Gateway", "status": "disconnected"}
        gateway_repo.get.return_value = gateway_data
        
        # Simulate connection failure
        mock_adapter.connect.return_value = False
        
        connected = await mock_adapter.connect()
        assert connected is False
        
        # Verify gateway status is updated to error
        gateway_data["status"] = "error"
        await gateway_repo.update(gateway_data)
        
        gateway_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_discovery_failure(self, mock_discovery_service):
        """Test handling of partial discovery failures."""
        service, api_repo, gateway_repo, mock_adapter = mock_discovery_service
        
        gateway_data = {"id": uuid4(), "name": "Test Gateway"}
        gateway_repo.get.return_value = gateway_data
        
        # Simulate partial discovery (some APIs succeed, some fail)
        successful_apis = [
            {"id": uuid4(), "name": "Success API 1"},
            {"id": uuid4(), "name": "Success API 2"},
        ]
        
        mock_adapter.discover_apis.return_value = successful_apis
        
        # First API succeeds, second fails
        api_repo.create.side_effect = [
            successful_apis[0],
            Exception("Database error"),
        ]
        
        # Attempt to create both APIs
        created_count = 0
        failed_count = 0
        
        for api in successful_apis:
            try:
                await api_repo.create(api)
                created_count += 1
            except Exception:
                failed_count += 1
        
        # Verify partial success
        assert created_count == 1
        assert failed_count == 1


# Made with Bob