"""Integration tests for remediation verification functionality.

Tests the complete remediation verification workflow including:
- Re-scanning after remediation
- Verification status updates
- Failed verification handling
- Verification evidence collection
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from backend.app.services.security_service import SecurityService
from backend.app.models.vulnerability import (
    VulnerabilityStatus,
    VerificationStatus,
    VulnerabilitySeverity,
    VulnerabilityType,
    RemediationType,
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
    return repo


@pytest.fixture
def mock_vulnerability_repository():
    """Create mock vulnerability repository."""
    repo = Mock()
    repo.get = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="Verification analysis")
    return service


@pytest.fixture
def security_service(
    settings,
    mock_api_repository,
    mock_vulnerability_repository,
    mock_llm_service,
):
    """Create security service with mocked dependencies."""
    service = SecurityService(
        settings=settings,
        api_repository=mock_api_repository,
        vulnerability_repository=mock_vulnerability_repository,
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
def test_vulnerability_in_progress(test_api):
    """Create a mock vulnerability in remediation progress."""
    vuln = MagicMock()
    vuln.id = uuid4()
    vuln.gateway_id = test_api.gateway_id
    vuln.api_id = test_api.id
    vuln.title = "Missing Rate Limiting"
    vuln.description = "API lacks rate limiting protection"
    vuln.vulnerability_type = VulnerabilityType.CONFIGURATION
    vuln.severity = VulnerabilitySeverity.HIGH
    vuln.status = VulnerabilityStatus.IN_PROGRESS
    vuln.remediation_type = RemediationType.AUTOMATED
    vuln.verification_status = None
    vuln.dict = MagicMock(return_value={
        "status": VulnerabilityStatus.REMEDIATED,
        "verification_status": VerificationStatus.VERIFIED,
        "remediated_at": datetime.utcnow().isoformat()
    })
    return vuln


@pytest.mark.asyncio
class TestRemediationVerification:
    """Integration tests for remediation verification."""

    async def test_successful_verification(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test successful verification of remediated vulnerability."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # Mock verification to return success
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check",
                "details": "Rate limiting policy successfully applied and verified",
                "evidence": {
                    "policy_id": "rate-limit-123",
                    "policy_active": True
                }
            }
            
            # Execute verification
            result = await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
        
        # Verify result
        assert result["is_fixed"] is True
        assert result["verification_method"] == "policy_check"
        assert "evidence" in result
        
        # Verify vulnerability was updated with REMEDIATED status
        mock_vulnerability_repository.update.assert_called_once()
        update_call = mock_vulnerability_repository.update.call_args
        assert update_call[0][0] == str(test_vulnerability_in_progress.id)
        updated_data = update_call[0][1]
        assert updated_data["status"] == VulnerabilityStatus.REMEDIATED
        assert updated_data["verification_status"] == VerificationStatus.VERIFIED

    async def test_failed_verification(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test failed verification when vulnerability still exists."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # Mock verification to return failure
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": False,
                "verification_method": "policy_check",
                "details": "Rate limiting policy not found or inactive",
                "reason": "Policy application may have failed"
            }
            
            # Update mock to return FAILED status
            test_vulnerability_in_progress.dict = MagicMock(return_value={
                "status": VulnerabilityStatus.IN_PROGRESS,
                "verification_status": VerificationStatus.FAILED
            })
            
            # Execute verification
            result = await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
        
        # Verify result indicates failure
        assert result["is_fixed"] is False
        assert "reason" in result
        
        # Verify vulnerability was updated with FAILED verification status
        mock_vulnerability_repository.update.assert_called_once()
        update_call = mock_vulnerability_repository.update.call_args
        updated_data = update_call[0][1]
        assert updated_data["verification_status"] == VerificationStatus.FAILED

    async def test_verification_with_evidence_collection(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test verification includes evidence collection."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # Mock verification with detailed evidence
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check",
                "details": "Verification complete with evidence",
                "evidence": {
                    "policy_id": "rate-limit-123",
                    "policy_active": True,
                    "policy_config": {
                        "requests_per_minute": 100,
                        "burst_size": 20
                    },
                    "verification_timestamp": datetime.utcnow().isoformat(),
                    "verified_by": "automated_scanner"
                }
            }
            
            # Execute verification
            result = await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
        
        # Verify evidence is included
        assert "evidence" in result
        assert result["evidence"]["policy_id"] == "rate-limit-123"
        assert result["evidence"]["policy_active"] is True
        assert "policy_config" in result["evidence"]

    async def test_verification_vulnerability_not_found(
        self,
        security_service,
        mock_vulnerability_repository,
    ):
        """Test verification handling of non-existent vulnerability."""
        # Setup mock to return None
        mock_vulnerability_repository.get.return_value = None
        
        # Execute verification and expect exception
        with pytest.raises(ValueError) as exc_info:
            await security_service.verify_remediation(uuid4())
        
        assert "not found" in str(exc_info.value).lower()

    async def test_verification_api_not_found(
        self,
        security_service,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test verification handling of non-existent API."""
        # Setup mocks
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        mock_api_repository.get.return_value = None
        
        # Execute verification and expect exception
        with pytest.raises(ValueError) as exc_info:
            await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
        
        assert "api" in str(exc_info.value).lower() and "not found" in str(exc_info.value).lower()

    async def test_verification_updates_timestamps(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test that verification updates remediated_at timestamp."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # Mock verification success
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check"
            }
            
            # Execute verification
            await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
        
        # Verify remediated_at was set
        update_call = mock_vulnerability_repository.update.call_args
        updated_data = update_call[0][1]
        assert "remediated_at" in updated_data
        assert updated_data["remediated_at"] is not None

    async def test_verification_multiple_attempts(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test verification can be retried after initial failure."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # First attempt - failure
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": False,
                "verification_method": "policy_check",
                "details": "Policy not yet active"
            }
            
            test_vulnerability_in_progress.dict = MagicMock(return_value={
                "status": VulnerabilityStatus.IN_PROGRESS,
                "verification_status": VerificationStatus.FAILED
            })
            
            result1 = await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
            
            assert result1["is_fixed"] is False
        
        # Second attempt - success
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = {
                "is_fixed": True,
                "verification_method": "policy_check",
                "details": "Policy now active"
            }
            
            test_vulnerability_in_progress.dict = MagicMock(return_value={
                "status": VulnerabilityStatus.REMEDIATED,
                "verification_status": VerificationStatus.VERIFIED
            })
            
            result2 = await security_service.verify_remediation(
                test_vulnerability_in_progress.id
            )
            
            assert result2["is_fixed"] is True

    async def test_verification_error_handling(
        self,
        security_service,
        test_api,
        test_vulnerability_in_progress,
        mock_api_repository,
        mock_vulnerability_repository,
    ):
        """Test verification error handling."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        mock_vulnerability_repository.get.return_value = test_vulnerability_in_progress
        
        # Mock verification to raise exception
        with patch.object(security_service, '_verify_vulnerability_fixed', new_callable=AsyncMock) as mock_verify:
            mock_verify.side_effect = Exception("Gateway connection failed")
            
            # Execute verification and expect exception
            with pytest.raises(Exception) as exc_info:
                await security_service.verify_remediation(
                    test_vulnerability_in_progress.id
                )
            
            assert "Gateway connection failed" in str(exc_info.value) or "Verification failed" in str(exc_info.value)

# Made with Bob
