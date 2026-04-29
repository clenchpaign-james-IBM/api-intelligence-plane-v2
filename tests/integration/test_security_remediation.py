"""Integration tests for automated security remediation functionality.

Tests the complete automated remediation workflow including:
- Automated remediation trigger
- Policy application via gateway adapter
- Remediation action tracking
- Status updates
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from backend.app.services.security_service import SecurityService
from backend.app.models.vulnerability import (
    VulnerabilityType,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    RemediationType,
    ConfigurationType,
    DetectionMethod,
)
from backend.app.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        OPENSEARCH_HOST="localhost",
        OPENSEARCH_PORT=9200,
        LLM_PROVIDER="openai",
        LLM_MODEL="gpt-4",
    )


@pytest.fixture
def mock_api_repository():
    """Create mock API repository."""
    repo = Mock()
    repo.get = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_vulnerability_repository():
    """Create mock vulnerability repository."""
    repo = Mock()
    repo.get = AsyncMock()
    repo.update = AsyncMock()
    repo.find_by_api_id = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_gateway_repository():
    """Create mock gateway repository."""
    repo = Mock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_gateway_adapter():
    """Create mock gateway adapter."""
    adapter = Mock()
    adapter.apply_policy = AsyncMock(return_value={
        "success": True,
        "policy_id": "test-policy-123",
        "message": "Policy applied successfully"
    })
    return adapter


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="AI remediation analysis")
    return service


@pytest.fixture
def security_service(
    settings,
    mock_api_repository,
    mock_vulnerability_repository,
    mock_gateway_repository,
    mock_gateway_adapter,
    mock_llm_service,
):
    """Create security service with mocked dependencies."""
    service = SecurityService(
        settings=settings,
        api_repository=mock_api_repository,
        vulnerability_repository=mock_vulnerability_repository,
        gateway_repository=mock_gateway_repository,
        gateway_adapter=mock_gateway_adapter,
        llm_service=mock_llm_service,
    )
    return service


@pytest.fixture
def test_api():
    """Create a mock test API."""
    api = MagicMock()
    api.id = uuid4()
    api.gateway_id = uuid4()
    api.name = "Test API"
    api.base_path = "/api/v1/test"
    return api


@pytest.fixture
def test_vulnerability_automated(test_api):
    """Create a mock test vulnerability that can be auto-remediated."""
    vuln = MagicMock()
    vuln.id = uuid4()
    vuln.gateway_id = test_api.gateway_id
    vuln.api_id = test_api.id
    vuln.title = "Missing Rate Limiting"
    vuln.description = "API lacks rate limiting protection"
    vuln.vulnerability_type = VulnerabilityType.CONFIGURATION
    vuln.configuration_type = ConfigurationType.RATE_LIMITING
    vuln.severity = VulnerabilitySeverity.HIGH
    vuln.status = VulnerabilityStatus.OPEN
    vuln.remediation_type = RemediationType.AUTOMATED
    vuln.recommended_remediation = {
        "actions": [
            {
                "action": "Apply rate limiting policy",
                "type": "configuration",
                "details": "Configure 100 requests per minute limit"
            }
        ],
        "estimated_time": "5 minutes",
        "risk_level": "low"
    }
    vuln.plan_source = "ai_agent"
    vuln.plan_version = "1.0"
    vuln.plan_status = "generated"
    vuln.remediation_actions = None
    vuln.dict = MagicMock(return_value={"status": VulnerabilityStatus.IN_PROGRESS, "plan_status": "approved"})
    return vuln


@pytest.fixture
def test_vulnerability_manual(test_api):
    """Create a mock test vulnerability that requires manual remediation."""
    vuln = MagicMock()
    vuln.id = uuid4()
    vuln.gateway_id = test_api.gateway_id
    vuln.api_id = test_api.id
    vuln.title = "Complex Authentication Issue"
    vuln.description = "Custom authentication logic requires manual review"
    vuln.vulnerability_type = VulnerabilityType.AUTHENTICATION
    vuln.severity = VulnerabilitySeverity.CRITICAL
    vuln.status = VulnerabilityStatus.OPEN
    vuln.remediation_type = RemediationType.MANUAL
    vuln.recommended_remediation = {
        "actions": [
            {
                "action": "Review authentication implementation",
                "type": "manual",
                "details": "Requires security team review"
            }
        ],
        "estimated_time": "2 hours",
        "risk_level": "high"
    }
    return vuln


@pytest.mark.asyncio
class TestSecurityRemediation:
    """Integration tests for automated security remediation."""

    async def test_automated_remediation_success(
        self,
        security_service,
        test_api,
        test_vulnerability_automated,
        mock_api_repository,
        mock_vulnerability_repository,
        mock_gateway_adapter,
    ):
        """Test successful automated remediation of a vulnerability."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        
        # Mock verification to return success
        with patch.object(security_service, 'verify_remediation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check",
                "details": "Rate limiting policy successfully applied"
            }
            
            # Execute remediation
            result = await security_service.remediate_vulnerability(
                test_vulnerability_automated.id
            )
        
        # Verify result
        assert result["status"] == "remediation_applied"
        assert result["vulnerability_id"] == str(test_vulnerability_automated.id)
        assert "remediation_result" in result
        assert "verification_result" in result
        
        # Verify gateway adapter was called
        mock_gateway_adapter.apply_policy.assert_called_once()
        
        # Verify vulnerability was updated
        mock_vulnerability_repository.update.assert_called()
        update_call = mock_vulnerability_repository.update.call_args
        assert update_call[0][0] == str(test_vulnerability_automated.id)

    async def test_manual_remediation_required(
        self,
        security_service,
        test_api,
        test_vulnerability_manual,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test that manual vulnerabilities return appropriate response."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_manual
        
        # Execute remediation
        result = await security_service.remediate_vulnerability(
            test_vulnerability_manual.id
        )
        
        # Verify result indicates manual intervention needed
        assert result["status"] == "manual_required"
        assert result["vulnerability_id"] == str(test_vulnerability_manual.id)
        assert "manual" in result["message"].lower()
        assert "recommended_plan" in result

    async def test_already_remediated_vulnerability(
        self,
        security_service,
        test_vulnerability_automated,
        mock_vulnerability_repository,
    ):
        """Test handling of already remediated vulnerability."""
        # Mark vulnerability as already remediated
        test_vulnerability_automated.status = VulnerabilityStatus.REMEDIATED
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        
        # Execute remediation
        result = await security_service.remediate_vulnerability(
            test_vulnerability_automated.id
        )
        
        # Verify result
        assert result["status"] == "already_remediated"
        assert "already" in result["message"].lower()

    async def test_remediation_with_custom_strategy(
        self,
        security_service,
        test_api,
        test_vulnerability_automated,
        mock_api_repository,
        mock_vulnerability_repository,
        mock_gateway_adapter,
    ):
        """Test remediation with custom strategy override."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        
        # Mock verification
        with patch.object(security_service, 'verify_remediation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check"
            }
            
            # Execute remediation with custom strategy
            result = await security_service.remediate_vulnerability(
                test_vulnerability_automated.id,
                remediation_strategy="aggressive"
            )
        
        # Verify result
        assert result["status"] == "remediation_applied"
        
        # Verify gateway adapter was called
        mock_gateway_adapter.apply_policy.assert_called_once()

    async def test_remediation_action_tracking(
        self,
        security_service,
        test_api,
        test_vulnerability_automated,
        mock_api_repository,
        mock_vulnerability_repository,
        mock_gateway_adapter,
    ):
        """Test that remediation actions are properly tracked."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        
        # Mock verification
        with patch.object(security_service, 'verify_remediation', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {"is_fixed": True}
            
            # Execute remediation
            await security_service.remediate_vulnerability(
                test_vulnerability_automated.id
            )
        
        # Verify vulnerability update included remediation actions
        update_call = mock_vulnerability_repository.update.call_args
        updated_data = update_call[0][1]
        
        # Check that status was updated to IN_PROGRESS
        assert updated_data.get("status") == VulnerabilityStatus.IN_PROGRESS
        
        # Check that plan_status was updated
        assert updated_data.get("plan_status") == "approved"

    async def test_remediation_failure_handling(
        self,
        security_service,
        test_api,
        test_vulnerability_automated,
        mock_api_repository,
        mock_vulnerability_repository,
        mock_gateway_adapter,
    ):
        """Test handling of remediation failures."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        
        # Make gateway adapter fail
        mock_gateway_adapter.apply_policy.side_effect = Exception("Gateway connection failed")
        
        # Execute remediation and expect exception
        with pytest.raises(Exception) as exc_info:
            await security_service.remediate_vulnerability(
                test_vulnerability_automated.id
            )
        
        assert "Gateway connection failed" in str(exc_info.value) or "Remediation failed" in str(exc_info.value)

    async def test_vulnerability_not_found(
        self,
        security_service,
        mock_vulnerability_repository,
    ):
        """Test handling of non-existent vulnerability."""
        # Setup mock to return None
        mock_vulnerability_repository.get.return_value = None
        
        # Execute remediation and expect exception
        with pytest.raises(ValueError) as exc_info:
            await security_service.remediate_vulnerability(uuid4())
        
        assert "not found" in str(exc_info.value).lower()

    async def test_api_not_found(
        self,
        security_service,
        test_vulnerability_automated,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test handling of non-existent API."""
        # Setup mocks
        mock_vulnerability_repository.get.return_value = test_vulnerability_automated
        mock_api_repository.get.return_value = None
        
        # Execute remediation and expect exception
        with pytest.raises(ValueError) as exc_info:
            await security_service.remediate_vulnerability(
                test_vulnerability_automated.id
            )
        
        assert "api" in str(exc_info.value).lower() and "not found" in str(exc_info.value).lower()

# Made with Bob
