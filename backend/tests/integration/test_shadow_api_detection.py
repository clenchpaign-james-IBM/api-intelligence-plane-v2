"""Integration tests for shadow API detection."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from app.scheduler.intelligence_metadata_jobs import (
    detect_shadow_apis_job,
    detect_shadow_apis_for_gateway,
)
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.models.gateway import Gateway, GatewayStatus, GatewayVendor
from app.models.base.api import API, DiscoveryMethod
from app.models.base.transaction import TransactionalLog


@pytest.fixture
def mock_gateway():
    """Create a mock gateway for testing."""
    gateway = Mock()
    gateway.id = uuid4()
    gateway.name = "Test Gateway"
    gateway.vendor = GatewayVendor.WEBMETHODS
    gateway.base_url = "http://localhost:8080"
    gateway.status = GatewayStatus.CONNECTED
    return gateway


@pytest.fixture
def mock_api(mock_gateway):
    """Create a mock API for testing."""
    return Mock(
        id=uuid4(),
        gateway_id=mock_gateway.id,
        name="users-api",
        base_path="/api/v1/users",
        version_info=Mock(current_version="v1"),
        endpoints=[
            Mock(path="/users"),
            Mock(path="/users/{id}"),
        ],
        intelligence_metadata=Mock(is_shadow=False),
    )


@pytest.fixture
def mock_transactional_logs(mock_gateway):
    """Create mock transactional logs for testing."""
    return [
        Mock(
            gateway_id=str(mock_gateway.id),
            request_path="/gateway/users-api/v1/users",
            timestamp=int(datetime.utcnow().timestamp() * 1000),
        ),
        Mock(
            gateway_id=str(mock_gateway.id),
            request_path="/gateway/users-api/v1/users/123",
            timestamp=int(datetime.utcnow().timestamp() * 1000),
        ),
        Mock(
            gateway_id=str(mock_gateway.id),
            request_path="/gateway/shadow-api/v1/secret",
            timestamp=int(datetime.utcnow().timestamp() * 1000),
        ),
    ]


class TestDetectShadowAPIsForGateway:
    """Tests for detect_shadow_apis_for_gateway function."""

    @pytest.mark.asyncio
    async def test_no_logs_returns_zero(self, mock_gateway):
        """Test that no logs returns zero detected APIs."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        log_repo.find_logs.return_value = ([], 0)
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        assert result == 0
        log_repo.find_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_paths_registered_returns_zero(
        self, mock_gateway, mock_api, mock_transactional_logs
    ):
        """Test that all registered paths returns zero shadow APIs."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        
        # Return logs with only registered paths
        registered_logs = mock_transactional_logs[:2]  # Only users-api paths
        log_repo.find_logs.return_value = (registered_logs, len(registered_logs))
        
        # Mock find_by_request_path to return API for registered paths
        api_repo.find_by_request_path.return_value = mock_api
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_detects_shadow_api(
        self, mock_gateway, mock_api, mock_transactional_logs
    ):
        """Test detection of shadow API."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        
        # Return all logs including shadow API
        log_repo.find_logs.return_value = (
            mock_transactional_logs,
            len(mock_transactional_logs)
        )
        
        # Mock find_by_request_path to return API for registered, None for shadow
        def mock_find_by_path(path, gateway_id):
            if "shadow-api" in path:
                return None  # Shadow API not registered
            return mock_api
        
        api_repo.find_by_request_path.side_effect = mock_find_by_path
        api_repo.create.return_value = Mock()
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        assert result == 1
        api_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_existing_shadow_api(
        self, mock_gateway, mock_transactional_logs
    ):
        """Test updating existing shadow API."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        
        # Return logs with shadow API
        shadow_logs = [mock_transactional_logs[2]]  # Only shadow-api path
        log_repo.find_logs.return_value = (shadow_logs, len(shadow_logs))
        
        # Mock existing shadow API
        existing_shadow = Mock(
            id=uuid4(),
            intelligence_metadata=Mock(is_shadow=True)
        )
        
        # First call returns None (for detection), second returns existing (for update)
        api_repo.find_by_request_path.side_effect = [None, existing_shadow]
        api_repo.update.return_value = Mock()
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        assert result == 1
        api_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_marks_existing_api_as_shadow(
        self, mock_gateway, mock_api, mock_transactional_logs
    ):
        """Test marking existing non-shadow API as shadow."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        
        # Return logs with shadow API
        shadow_logs = [mock_transactional_logs[2]]
        log_repo.find_logs.return_value = (shadow_logs, len(shadow_logs))
        
        # Mock existing non-shadow API
        existing_api = Mock(
            id=uuid4(),
            intelligence_metadata=Mock(is_shadow=False)
        )
        
        # Both calls return existing API
        api_repo.find_by_request_path.return_value = existing_api
        api_repo.update.return_value = Mock()
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        assert result == 1
        api_repo.update.assert_called_once()
        
        # Verify update includes is_shadow=True
        update_call = api_repo.update.call_args
        assert "intelligence_metadata.is_shadow" in str(update_call)


class TestDetectShadowAPIsJob:
    """Tests for detect_shadow_apis_job function."""

    @pytest.mark.asyncio
    async def test_no_gateways_returns_early(self):
        """Test that no gateways returns early."""
        with patch('app.scheduler.intelligence_metadata_jobs.GatewayRepository') as MockGatewayRepo:
            mock_repo = Mock()
            mock_repo.list_all.return_value = ([], 0)
            MockGatewayRepo.return_value = mock_repo
            
            await detect_shadow_apis_job()
            
            mock_repo.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_processes_multiple_gateways(self, mock_gateway):
        """Test processing multiple gateways."""
        gateway1 = mock_gateway
        gateway2 = Mock()
        gateway2.id = uuid4()
        gateway2.name = "Test Gateway 2"
        gateway2.vendor = GatewayVendor.WEBMETHODS
        gateway2.base_url = "http://localhost:8081"
        gateway2.status = GatewayStatus.CONNECTED
        
        with patch('app.scheduler.intelligence_metadata_jobs.GatewayRepository') as MockGatewayRepo, \
             patch('app.scheduler.intelligence_metadata_jobs.detect_shadow_apis_for_gateway') as mock_detect:
            
            mock_repo = Mock()
            mock_repo.list_all.return_value = ([gateway1, gateway2], 2)
            MockGatewayRepo.return_value = mock_repo
            
            mock_detect.return_value = 1
            
            await detect_shadow_apis_job()
            
            assert mock_detect.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_gateway_errors_gracefully(self, mock_gateway):
        """Test that errors in one gateway don't stop processing others."""
        gateway1 = mock_gateway
        gateway2 = Mock()
        gateway2.id = uuid4()
        gateway2.name = "Test Gateway 2"
        gateway2.vendor = GatewayVendor.WEBMETHODS
        gateway2.base_url = "http://localhost:8081"
        gateway2.status = GatewayStatus.CONNECTED
        
        with patch('app.scheduler.intelligence_metadata_jobs.GatewayRepository') as MockGatewayRepo, \
             patch('app.scheduler.intelligence_metadata_jobs.detect_shadow_apis_for_gateway') as mock_detect:
            
            mock_repo = Mock()
            mock_repo.list_all.return_value = ([gateway1, gateway2], 2)
            MockGatewayRepo.return_value = mock_repo
            
            # First gateway fails, second succeeds
            mock_detect.side_effect = [Exception("Test error"), 1]
            
            await detect_shadow_apis_job()
            
            # Should still process both gateways
            assert mock_detect.call_count == 2


class TestPathMatchingIntegration:
    """Integration tests for path matching in shadow API detection."""

    @pytest.mark.asyncio
    async def test_matches_path_with_parameters(self, mock_gateway):
        """Test matching paths with parameters."""
        api_repo = Mock(spec=APIRepository)
        log_repo = Mock(spec=TransactionalLogRepository)
        
        # Create logs with parameterized paths
        logs = [
            Mock(
                gateway_id=str(mock_gateway.id),
                request_path="/gateway/users-api/v1/users/123",
            ),
            Mock(
                gateway_id=str(mock_gateway.id),
                request_path="/gateway/users-api/v1/users/456/profile",
            ),
        ]
        log_repo.find_logs.return_value = (logs, len(logs))
        
        # Mock API with parameterized endpoints
        mock_api = Mock(
            endpoints=[
                Mock(path="/users/{id}"),
                Mock(path="/users/{id}/profile"),
            ]
        )
        api_repo.find_by_request_path.return_value = mock_api
        
        result = await detect_shadow_apis_for_gateway(
            mock_gateway, api_repo, log_repo
        )
        
        # Should not detect as shadow since patterns match
        assert result == 0

    @pytest.mark.asyncio
    async def test_different_gateway_routing_schemes(self):
        """Test handling different gateway routing schemes."""
        # Test with different path formats
        test_cases = [
            "/gateway/api/v1/resource",
            "/api/v1/resource",
            "/api-gateway/api/v1/resource",
        ]
        
        for path in test_cases:
            from app.utils.path_matcher import parse_request_path
            result = parse_request_path(path)
            assert result is not None, f"Failed to parse: {path}"

# Made with Bob
