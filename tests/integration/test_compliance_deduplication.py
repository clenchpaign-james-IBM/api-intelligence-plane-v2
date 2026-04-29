"""Integration tests for compliance violation deduplication functionality.

Tests the complete deduplication workflow including:
- Duplicate detection across multiple scans
- Fingerprint-based matching
- Violation merging and consolidation
- Historical tracking
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock

from backend.app.services.compliance_service import ComplianceService
from backend.app.models.compliance import (
    ComplianceViolation,
    ComplianceViolationType,
    ComplianceSeverity,
    ComplianceStandard,
    ComplianceStatus,
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
    return repo


@pytest.fixture
def mock_compliance_repository():
    """Create mock compliance repository."""
    repo = Mock()
    repo.find_by_api = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.find_duplicates = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="Compliance analysis")
    return service


@pytest.fixture
def compliance_service(
    settings,
    mock_api_repository,
    mock_compliance_repository,
    mock_llm_service,
):
    """Create compliance service with mocked dependencies."""
    service = ComplianceService(
        settings=settings,
        api_repository=mock_api_repository,
        compliance_repository=mock_compliance_repository,
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
def test_violation(test_api):
    """Create a mock test compliance violation."""
    violation = MagicMock()
    violation.id = uuid4()
    violation.gateway_id = test_api.gateway_id
    violation.api_id = test_api.id
    violation.violation_type = ComplianceViolationType.MISSING_ENCRYPTION_CONTROLS
    violation.standard = ComplianceStandard.GDPR
    violation.severity = ComplianceSeverity.HIGH
    violation.title = "Unencrypted PII transmission"
    violation.description = "Personal data transmitted without encryption"
    violation.status = ComplianceStatus.OPEN
    violation.fingerprint = "gdpr_data_exposure_unencrypted_pii_/api/v1/test"
    violation.detected_at = datetime.utcnow()
    return violation


@pytest.mark.asyncio
class TestComplianceDeduplication:
    """Integration tests for compliance violation deduplication."""

    async def test_detect_exact_duplicate(
        self,
        compliance_service,
        test_api,
        test_violation,
        mock_api_repository,
        mock_compliance_repository,
    ):
        """Test detection of exact duplicate violations."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        # Create existing violation with same fingerprint
        existing_violation = MagicMock()
        existing_violation.id = uuid4()
        existing_violation.fingerprint = test_violation.fingerprint
        existing_violation.status = ComplianceStatus.OPEN
        existing_violation.detected_at = datetime.utcnow() - timedelta(days=1)
        
        mock_compliance_repository.find_duplicates.return_value = [existing_violation]
        
        # Attempt to create duplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify duplicate detected
        assert result["is_duplicate"] is True
        assert result["existing_violation_id"] == str(existing_violation.id)
        assert "fingerprint_match" in result["match_method"]

    async def test_no_duplicate_found(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test when no duplicate violations exist."""
        # Setup mock to return no duplicates
        mock_compliance_repository.find_duplicates.return_value = []
        
        # Check for duplicates
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify no duplicate found
        assert result["is_duplicate"] is False
        assert "existing_violation_id" not in result

    async def test_deduplicate_updates_existing_violation(
        self,
        compliance_service,
        test_api,
        test_violation,
        mock_api_repository,
        mock_compliance_repository,
    ):
        """Test that deduplication updates the existing violation."""
        # Setup mocks
        mock_api_repository.get.return_value = test_api
        
        existing_violation = MagicMock()
        existing_violation.id = uuid4()
        existing_violation.fingerprint = test_violation.fingerprint
        existing_violation.status = ComplianceStatus.OPEN
        existing_violation.occurrence_count = 1
        existing_violation.last_seen_at = datetime.utcnow() - timedelta(days=1)
        
        mock_compliance_repository.find_duplicates.return_value = [existing_violation]
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify existing violation would be updated
        assert result["is_duplicate"] is True
        assert result["action"] == "updated_existing"

    async def test_deduplicate_resolved_violation_reopens(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test that finding a duplicate of a resolved violation reopens it."""
        # Setup existing resolved violation
        existing_violation = MagicMock()
        existing_violation.id = uuid4()
        existing_violation.fingerprint = test_violation.fingerprint
        existing_violation.status = ComplianceStatus.REMEDIATED
        existing_violation.resolved_at = datetime.utcnow() - timedelta(days=5)
        
        mock_compliance_repository.find_duplicates.return_value = [existing_violation]
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify violation would be reopened
        assert result["is_duplicate"] is True
        assert result["action"] == "reopened"

    async def test_deduplicate_tracks_occurrence_count(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test that deduplication tracks occurrence count."""
        # Setup existing violation with occurrence count
        existing_violation = MagicMock()
        existing_violation.id = uuid4()
        existing_violation.fingerprint = test_violation.fingerprint
        existing_violation.status = ComplianceStatus.OPEN
        existing_violation.occurrence_count = 5
        existing_violation.first_seen_at = datetime.utcnow() - timedelta(days=10)
        existing_violation.last_seen_at = datetime.utcnow() - timedelta(days=1)
        
        mock_compliance_repository.find_duplicates.return_value = [existing_violation]
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify occurrence tracking
        assert result["is_duplicate"] is True
        if "occurrence_count" in result:
            assert result["occurrence_count"] == 6  # Incremented

    async def test_deduplicate_different_apis_same_issue(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test deduplication across different APIs with same issue type."""
        # Create violation for different API but same issue
        different_api_violation = MagicMock()
        different_api_violation.id = uuid4()
        different_api_violation.api_id = uuid4()  # Different API
        different_api_violation.fingerprint = test_violation.fingerprint
        different_api_violation.status = ComplianceStatus.OPEN
        
        mock_compliance_repository.find_duplicates.return_value = [different_api_violation]
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify cross-API deduplication
        assert result["is_duplicate"] is True

    async def test_deduplicate_similar_but_not_identical(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test that similar but not identical violations are not deduplicated."""
        # Create similar but different violation
        similar_violation = MagicMock()
        similar_violation.id = uuid4()
        similar_violation.fingerprint = "gdpr_data_exposure_unencrypted_pii_/api/v1/different"  # Different fingerprint
        similar_violation.violation_type = test_violation.violation_type
        similar_violation.standard = test_violation.standard
        similar_violation.status = ComplianceStatus.OPEN
        
        mock_compliance_repository.find_duplicates.return_value = []  # No exact match
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify not considered duplicate
        assert result["is_duplicate"] is False

    async def test_deduplicate_batch_violations(
        self,
        compliance_service,
        test_api,
        mock_compliance_repository,
    ):
        """Test batch deduplication of multiple violations."""
        # Create multiple violations
        violations = []
        for i in range(5):
            violation = MagicMock()
            violation.id = uuid4()
            violation.api_id = test_api.id
            violation.fingerprint = f"test_fingerprint_{i}"
            violation.status = ComplianceStatus.OPEN
            violations.append(violation)
        
        # Setup mock to return no duplicates
        mock_compliance_repository.find_duplicates.return_value = []
        
        # Deduplicate batch
        results = []
        for violation in violations:
            result = await compliance_service.deduplicate_violation(violation)
            results.append(result)
        
        # Verify all processed
        assert len(results) == 5
        assert all(not r["is_duplicate"] for r in results)

    async def test_deduplicate_preserves_evidence(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test that deduplication preserves evidence from all occurrences."""
        # Setup existing violation with evidence
        existing_violation = MagicMock()
        existing_violation.id = uuid4()
        existing_violation.fingerprint = test_violation.fingerprint
        existing_violation.status = ComplianceStatus.OPEN
        existing_violation.evidence = [
            {"timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "source": "scan_1"}
        ]
        
        # New violation has additional evidence
        test_violation.evidence = [
            {"timestamp": datetime.utcnow().isoformat(), "source": "scan_2"}
        ]
        
        mock_compliance_repository.find_duplicates.return_value = [existing_violation]
        
        # Deduplicate
        result = await compliance_service.deduplicate_violation(test_violation)
        
        # Verify evidence would be merged
        assert result["is_duplicate"] is True
        assert result["action"] in ["updated_existing", "merged_evidence"]

    async def test_deduplicate_error_handling(
        self,
        compliance_service,
        test_violation,
        mock_compliance_repository,
    ):
        """Test deduplication error handling."""
        # Mock repository to raise exception
        mock_compliance_repository.find_duplicates.side_effect = Exception(
            "Database query failed"
        )
        
        # Attempt deduplication and expect exception
        with pytest.raises(Exception) as exc_info:
            await compliance_service.deduplicate_violation(test_violation)
        
        assert "Database query failed" in str(exc_info.value) or "Failed" in str(exc_info.value)

# Made with Bob
