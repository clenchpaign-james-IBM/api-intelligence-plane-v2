"""Integration tests for compliance scanning functionality.

Tests the complete compliance scanning workflow including:
- AI-driven compliance detection for 5 standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
- Multi-source data analysis (API metadata + metrics + traffic patterns)
- Compliance posture reporting
- Audit report generation
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.compliance_service import ComplianceService
from backend.app.agents.compliance_agent import ComplianceAgent
from backend.app.models.api import (
    API,
    AuthenticationType,
    Endpoint,
    DiscoveryMethod,
    APIStatus,
    CurrentMetrics,
)
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
    repo.find_all = AsyncMock()
    return repo


@pytest.fixture
def mock_compliance_repository():
    """Create mock compliance repository."""
    repo = Mock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.find_by_api = AsyncMock(return_value=[])
    repo.find_by_standard = AsyncMock(return_value=[])
    repo.find_open_violations = AsyncMock(return_value=[])
    repo.get_compliance_posture = AsyncMock()
    repo.generate_audit_report_data = AsyncMock()
    return repo


@pytest.fixture
def mock_metrics_repository():
    """Create mock metrics repository."""
    repo = Mock()
    repo.find_by_api = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_gateway_repository():
    """Create mock gateway repository."""
    repo = Mock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = Mock()
    service.complete = AsyncMock(return_value="AI compliance analysis result")
    return service


@pytest.fixture
def mock_compliance_agent(mock_llm_service, mock_metrics_repository):
    """Create mock compliance agent."""
    agent = ComplianceAgent(mock_llm_service, mock_metrics_repository)
    return agent


@pytest.fixture
def compliance_service(
    settings,
    mock_api_repository,
    mock_compliance_repository,
    mock_llm_service,
    mock_compliance_agent,
    mock_metrics_repository,
    mock_gateway_repository,
):
    """Create compliance service instance."""
    return ComplianceService(
        settings=settings,
        api_repository=mock_api_repository,
        compliance_repository=mock_compliance_repository,
        llm_service=mock_llm_service,
        compliance_agent=mock_compliance_agent,
        metrics_repository=mock_metrics_repository,
        gateway_repository=mock_gateway_repository,
    )


def create_test_api(
    name: str = "Test API",
    base_path: str = "/api/v1/test",
    auth_type: AuthenticationType = AuthenticationType.NONE,
    tags: list[str] | None = None,
) -> API:
    """Helper to create test API with all required fields."""
    return API(
        id=uuid4(),
        gateway_id=uuid4(),
        name=name,
        version="v1",
        base_path=base_path,
        endpoints=[
            Endpoint(
                path=f"{base_path}/data",
                method="GET",
                description="Get data",
            ),
        ],
        methods=["GET"],
        authentication_type=auth_type,
        authentication_config=None,
        ownership=None,
        tags=tags or [],
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        status=APIStatus.ACTIVE,
        health_score=85.0,
        current_metrics=CurrentMetrics(
            response_time_p50=50.0,
            response_time_p95=150.0,
            response_time_p99=250.0,
            error_rate=0.01,
            throughput=100.0,
            availability=99.5,
            last_error=None,
            measured_at=datetime.utcnow(),
        ),
        security_policies=None,
        metadata=None,
    )


class TestGDPRCompliance:
    """Test GDPR compliance detection."""

    @pytest.mark.asyncio
    async def test_detect_gdpr_data_protection_issues(
        self, compliance_service, mock_api_repository
    ):
        """Test GDPR data protection compliance detection."""
        api = create_test_api(
            name="User Profile API",
            base_path="/api/v1/users",
            tags=["users", "personal-data"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.GDPR]
        )

        assert result is not None
        assert "violations" in result
        assert len(result["violations"]) > 0
        
        # Should detect GDPR violations
        gdpr_violations = [
            v for v in result["violations"]
            if v.standard == ComplianceStandard.GDPR
        ]
        assert len(gdpr_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_gdpr_security_of_processing(
        self, compliance_service, mock_api_repository
    ):
        """Test GDPR security of processing compliance."""
        api = create_test_api(
            name="Marketing API",
            base_path="/api/v1/marketing",
            tags=["marketing", "consent"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.GDPR]
        )

        assert result is not None
        
        # Should detect GDPR security issues
        security_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.GDPR_SECURITY_OF_PROCESSING
        ]
        assert len(security_violations) > 0


class TestHIPAACompliance:
    """Test HIPAA compliance detection."""

    @pytest.mark.asyncio
    async def test_detect_hipaa_access_control_issues(
        self, compliance_service, mock_api_repository
    ):
        """Test HIPAA access control compliance."""
        api = create_test_api(
            name="Patient Records API",
            base_path="/api/v1/health",
            tags=["healthcare", "medical"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.HIPAA]
        )

        assert result is not None
        assert "violations" in result
        
        # Should detect HIPAA violations
        hipaa_violations = [
            v for v in result["violations"]
            if v.standard == ComplianceStandard.HIPAA
        ]
        assert len(hipaa_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_hipaa_transmission_security(
        self, compliance_service, mock_api_repository
    ):
        """Test HIPAA transmission security compliance."""
        api = create_test_api(
            name="Medical Records API",
            base_path="/api/v1/medical",
            auth_type=AuthenticationType.BASIC,  # Weak auth
            tags=["healthcare", "records"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.HIPAA]
        )

        assert result is not None
        
        # Should detect transmission security issues
        transmission_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY
        ]
        assert len(transmission_violations) > 0


class TestPCIDSSCompliance:
    """Test PCI-DSS compliance detection."""

    @pytest.mark.asyncio
    async def test_detect_pci_dss_network_security_issues(
        self, compliance_service, mock_api_repository
    ):
        """Test PCI-DSS network security compliance."""
        api = create_test_api(
            name="Payment API",
            base_path="/api/v1/payments",
            tags=["payment", "financial"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.PCI_DSS]
        )

        assert result is not None
        assert "violations" in result
        
        # Should detect PCI-DSS violations
        pci_violations = [
            v for v in result["violations"]
            if v.standard == ComplianceStandard.PCI_DSS
        ]
        assert len(pci_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_pci_dss_encryption_in_transit(
        self, compliance_service, mock_api_repository
    ):
        """Test PCI-DSS encryption in transit compliance."""
        api = create_test_api(
            name="Card Storage API",
            base_path="/api/v1/cards",
            auth_type=AuthenticationType.API_KEY,
            tags=["payment", "storage"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.PCI_DSS]
        )

        assert result is not None
        
        # Should detect encryption issues
        encryption_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.PCI_DSS_ENCRYPTION_IN_TRANSIT
        ]
        assert len(encryption_violations) > 0


class TestSOC2Compliance:
    """Test SOC2 compliance detection."""

    @pytest.mark.asyncio
    async def test_detect_soc2_security_availability(
        self, compliance_service, mock_api_repository
    ):
        """Test SOC2 security availability compliance."""
        api = create_test_api(
            name="User Profile API",
            base_path="/api/v1/users",
            tags=["users", "personal-data"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.SOC2]
        )

        assert result is not None
        assert "violations" in result
        
        # Should detect SOC2 violations
        soc2_violations = [
            v for v in result["violations"]
            if v.standard == ComplianceStandard.SOC2
        ]
        assert len(soc2_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_soc2_system_monitoring(
        self, compliance_service, mock_api_repository
    ):
        """Test SOC2 system monitoring compliance."""
        api = create_test_api(
            name="Admin API",
            base_path="/api/v1/admin",
            auth_type=AuthenticationType.API_KEY,
            tags=["admin", "config"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.SOC2]
        )

        assert result is not None
        
        # Should detect monitoring issues
        monitoring_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.SOC2_SYSTEM_MONITORING
        ]
        assert len(monitoring_violations) > 0


class TestISO27001Compliance:
    """Test ISO 27001 compliance detection."""

    @pytest.mark.asyncio
    async def test_detect_iso27001_access_control(
        self, compliance_service, mock_api_repository
    ):
        """Test ISO 27001 access control compliance."""
        api = create_test_api(
            name="User Profile API",
            base_path="/api/v1/users",
            tags=["users", "personal-data"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.ISO_27001]
        )

        assert result is not None
        assert "violations" in result
        
        # Should detect ISO 27001 violations
        iso_violations = [
            v for v in result["violations"]
            if v.standard == ComplianceStandard.ISO_27001
        ]
        assert len(iso_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_iso27001_cryptography(
        self, compliance_service, mock_api_repository
    ):
        """Test ISO 27001 cryptography compliance."""
        api = create_test_api(
            name="Financial Transactions API",
            base_path="/api/v1/transactions",
            tags=["financial", "transactions"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.ISO_27001]
        )

        assert result is not None
        
        # Should detect cryptography issues
        crypto_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.ISO_27001_CRYPTOGRAPHY
        ]
        assert len(crypto_violations) > 0


class TestMultiStandardScanning:
    """Test scanning for multiple compliance standards."""

    @pytest.mark.asyncio
    async def test_scan_all_standards(
        self, compliance_service, mock_api_repository
    ):
        """Test scanning for all compliance standards."""
        api = create_test_api()
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(api.id)

        assert result is not None
        assert "violations" in result
        
        # Should check all standards
        standards_found = set(v.standard for v in result["violations"])
        assert len(standards_found) > 0

    @pytest.mark.asyncio
    async def test_scan_specific_standards(
        self, compliance_service, mock_api_repository
    ):
        """Test scanning for specific compliance standards."""
        api = create_test_api()
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.GDPR, ComplianceStandard.SOC2]
        )

        assert result is not None
        assert "violations" in result
        
        # Should only check specified standards
        standards_found = set(v.standard for v in result["violations"])
        assert standards_found.issubset({ComplianceStandard.GDPR, ComplianceStandard.SOC2})


class TestCrossStandardViolations:
    """Test cross-standard violation detection."""

    @pytest.mark.asyncio
    async def test_detect_insufficient_logging_monitoring(
        self, compliance_service, mock_api_repository
    ):
        """Test detection of insufficient logging/monitoring."""
        api = create_test_api(
            name="Critical API",
            base_path="/api/v1/critical",
            tags=["critical", "sensitive"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(api.id)

        assert result is not None
        
        # Should detect logging/monitoring issues
        logging_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.INSUFFICIENT_LOGGING_MONITORING
        ]
        assert len(logging_violations) > 0

    @pytest.mark.asyncio
    async def test_detect_inadequate_access_controls(
        self, compliance_service, mock_api_repository
    ):
        """Test detection of inadequate access controls."""
        api = create_test_api(
            name="Admin API",
            base_path="/api/v1/admin",
            auth_type=AuthenticationType.NONE,
            tags=["admin", "privileged"],
        )
        mock_api_repository.get.return_value = api

        result = await compliance_service.scan_api_compliance(api.id)

        assert result is not None
        
        # Should detect access control issues
        access_violations = [
            v for v in result["violations"]
            if v.violation_type == ComplianceViolationType.INADEQUATE_ACCESS_CONTROLS
        ]
        assert len(access_violations) > 0


class TestCompliancePosture:
    """Test compliance posture reporting."""

    @pytest.mark.asyncio
    async def test_get_compliance_posture(
        self, compliance_service, mock_compliance_repository
    ):
        """Test getting compliance posture."""
        # Mock posture data
        mock_compliance_repository.get_compliance_posture.return_value = {
            "total_violations": 25,
            "critical_violations": 5,
            "high_violations": 10,
            "medium_violations": 8,
            "low_violations": 2,
            "by_standard": {
                "GDPR": 8,
                "HIPAA": 5,
                "PCI_DSS": 4,
                "SOC2": 5,
                "ISO_27001": 3,
            },
            "compliance_score": 72.5,
        }

        result = await compliance_service.get_compliance_posture()

        assert result is not None
        assert result["total_violations"] == 25
        assert result["compliance_score"] == 72.5
        assert "by_standard" in result

    @pytest.mark.asyncio
    async def test_get_compliance_posture_by_standard(
        self, compliance_service, mock_compliance_repository
    ):
        """Test getting compliance posture for specific standard."""
        # Mock standard-specific posture
        mock_compliance_repository.get_compliance_posture.return_value = {
            "total_violations": 8,
            "critical_violations": 2,
            "high_violations": 3,
            "medium_violations": 2,
            "low_violations": 1,
            "compliance_score": 68.0,
        }

        result = await compliance_service.get_compliance_posture(
            standard=ComplianceStandard.GDPR
        )

        assert result is not None
        assert result["total_violations"] == 8
        assert result["compliance_score"] == 68.0


class TestAuditReportGeneration:
    """Test audit report generation."""

    @pytest.mark.asyncio
    async def test_generate_audit_report(
        self, compliance_service, mock_compliance_repository
    ):
        """Test generating audit report."""
        # Mock audit report data
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "total_apis": 50,
            "scanned_apis": 48,
            "total_violations": 25,
            "violations_by_severity": {
                "critical": 5,
                "high": 10,
                "medium": 8,
                "low": 2,
            },
            "violations_by_standard": {
                "GDPR": 8,
                "HIPAA": 5,
                "PCI_DSS": 4,
                "SOC2": 5,
                "ISO_27001": 3,
            },
        }

        result = await compliance_service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            standards=[ComplianceStandard.GDPR, ComplianceStandard.HIPAA]
        )

        assert result is not None
        assert "report_id" in result
        assert "summary" in result
        assert result["summary"]["total_apis"] == 50
        assert result["summary"]["total_violations"] == 25

    @pytest.mark.asyncio
    async def test_generate_audit_report_with_ai_summary(
        self, compliance_service, mock_compliance_repository, mock_llm_service
    ):
        """Test generating audit report with AI-generated executive summary."""
        # Mock audit report data
        mock_compliance_repository.generate_audit_report_data.return_value = {
            "total_apis": 50,
            "scanned_apis": 48,
            "total_violations": 25,
            "violations_by_severity": {
                "critical": 5,
                "high": 10,
                "medium": 8,
                "low": 2,
            },
        }

        # Mock AI summary
        mock_llm_service.complete.return_value = "Executive Summary: The organization shows moderate compliance posture with 25 violations identified across 48 APIs."

        result = await compliance_service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )

        assert result is not None
        assert "executive_summary" in result
        assert "moderate compliance posture" in result["executive_summary"].lower()


# Made with Bob