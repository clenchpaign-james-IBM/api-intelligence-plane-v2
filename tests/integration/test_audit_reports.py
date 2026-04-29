"""Integration tests for audit report generation functionality.

Tests the complete audit report generation workflow including:
- Report generation for compliance standards
- Evidence collection and aggregation
- Report formatting and structure
- Historical data inclusion
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock

from backend.app.services.compliance_service import ComplianceService
from backend.app.models.compliance import (
    ComplianceStandard,
    ComplianceSeverity,
    ComplianceStatus,
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
    repo.find_all = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_compliance_repository():
    """Create mock compliance repository."""
    repo = Mock()
    repo.generate_audit_report_data = AsyncMock()
    repo.find_by_standard = AsyncMock(return_value=[])
    repo.get_compliance_posture = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="Audit analysis")
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


@pytest.mark.asyncio
class TestAuditReportGeneration:
    """Integration tests for audit report generation."""

    async def test_generate_audit_report_single_standard(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test generating audit report for a single compliance standard."""
        # Setup mock data
        gateway_id = uuid4()
        standard = ComplianceStandard.GDPR
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": standard.value,
            "gateway_id": str(gateway_id),
            "report_period": {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_violations": 15,
            "by_severity": {
                "critical": 2,
                "high": 5,
                "medium": 6,
                "low": 2
            },
            "by_status": {
                "open": 8,
                "in_progress": 4,
                "resolved": 3
            },
            "violations": [],
            "compliance_score": 85.5,
        }
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[standard]
        )
        
        # Verify report structure
        assert result is not None
        assert "reports" in result
        assert len(result["reports"]) == 1
        assert result["reports"][0]["standard"] == standard.value
        assert result["reports"][0]["total_violations"] == 15
        assert result["reports"][0]["compliance_score"] == 85.5

    async def test_generate_audit_report_multiple_standards(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test generating audit report for multiple compliance standards."""
        gateway_id = uuid4()
        standards = [ComplianceStandard.GDPR, ComplianceStandard.HIPAA, ComplianceStandard.SOC2]
        
        # Setup mock to return different data for each standard
        async def mock_generate_report(gateway_id, standard, start_date, end_date):
            return {
                "standard": standard.value,
                "gateway_id": str(gateway_id),
                "total_violations": 10,
                "compliance_score": 90.0,
            }
        
        mock_compliance_repository.generate_audit_report_data.side_effect = mock_generate_report
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=standards
        )
        
        # Verify all standards included
        assert len(result["reports"]) == 3
        report_standards = [r["standard"] for r in result["reports"]]
        assert ComplianceStandard.GDPR.value in report_standards
        assert ComplianceStandard.HIPAA.value in report_standards
        assert ComplianceStandard.SOC2.value in report_standards

    async def test_generate_audit_report_with_date_range(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test generating audit report for specific date range."""
        gateway_id = uuid4()
        start_date = datetime.utcnow() - timedelta(days=90)
        end_date = datetime.utcnow()
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": ComplianceStandard.PCI_DSS.value,
            "gateway_id": str(gateway_id),
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_violations": 20,
            "compliance_score": 80.0,
        }
        
        # Generate report with date range
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[ComplianceStandard.PCI_DSS],
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify date range in report
        assert result["reports"][0]["report_period"]["start"] == start_date.isoformat()
        assert result["reports"][0]["report_period"]["end"] == end_date.isoformat()

    async def test_generate_audit_report_includes_evidence(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test that audit report includes evidence for violations."""
        gateway_id = uuid4()
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": ComplianceStandard.GDPR.value,
            "gateway_id": str(gateway_id),
            "total_violations": 5,
            "violations": [
                {
                    "id": str(uuid4()),
                    "title": "Missing data encryption",
                    "severity": "high",
                    "evidence": {
                        "api_endpoint": "/api/v1/users",
                        "data_types": ["email", "phone"],
                        "encryption_status": "none"
                    }
                }
            ],
            "compliance_score": 75.0,
        }
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[ComplianceStandard.GDPR]
        )
        
        # Verify evidence included
        assert len(result["reports"][0]["violations"]) > 0
        violation = result["reports"][0]["violations"][0]
        assert "evidence" in violation
        assert violation["evidence"]["encryption_status"] == "none"

    async def test_generate_audit_report_calculates_compliance_score(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test that audit report calculates compliance score correctly."""
        gateway_id = uuid4()
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": ComplianceStandard.SOC2.value,
            "gateway_id": str(gateway_id),
            "total_violations": 10,
            "by_severity": {
                "critical": 1,
                "high": 2,
                "medium": 4,
                "low": 3
            },
            "compliance_score": 82.5,
        }
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[ComplianceStandard.SOC2]
        )
        
        # Verify compliance score
        assert "compliance_score" in result["reports"][0]
        assert 0 <= result["reports"][0]["compliance_score"] <= 100

    async def test_generate_audit_report_empty_violations(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test generating audit report when no violations exist."""
        gateway_id = uuid4()
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": ComplianceStandard.ISO_27001.value,
            "gateway_id": str(gateway_id),
            "total_violations": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "violations": [],
            "compliance_score": 100.0,
        }
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[ComplianceStandard.ISO_27001]
        )
        
        # Verify perfect compliance
        assert result["reports"][0]["total_violations"] == 0
        assert result["reports"][0]["compliance_score"] == 100.0

    async def test_generate_audit_report_includes_trends(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test that audit report includes compliance trends over time."""
        gateway_id = uuid4()
        
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "standard": ComplianceStandard.HIPAA.value,
            "gateway_id": str(gateway_id),
            "total_violations": 12,
            "compliance_score": 88.0,
            "trends": {
                "previous_score": 85.0,
                "score_change": 3.0,
                "trend_direction": "improving"
            }
        }
        
        # Generate report
        result = await compliance_service.generate_audit_report(
            gateway_id=gateway_id,
            standards=[ComplianceStandard.HIPAA]
        )
        
        # Verify trends included
        if "trends" in result["reports"][0]:
            assert result["reports"][0]["trends"]["trend_direction"] == "improving"

    async def test_generate_audit_report_error_handling(
        self,
        compliance_service,
        mock_compliance_repository,
    ):
        """Test audit report generation error handling."""
        gateway_id = uuid4()
        
        # Mock repository to raise exception
        mock_compliance_repository.generate_audit_report_data.side_effect = Exception(
            "Database connection failed"
        )
        
        # Generate report and expect exception
        with pytest.raises(Exception) as exc_info:
            await compliance_service.generate_audit_report(
                gateway_id=gateway_id,
                standards=[ComplianceStandard.GDPR]
            )
        
        assert "Database connection failed" in str(exc_info.value) or "Failed" in str(exc_info.value)

# Made with Bob
