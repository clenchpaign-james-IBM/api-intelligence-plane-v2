"""End-to-end tests for compliance audit workflow.

Tests the complete audit workflow including:
- Compliance violation detection across multiple APIs
- Audit report generation with AI-enhanced summaries
- Compliance posture tracking over time
- Multi-standard compliance reporting
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
def compliance_service_with_mocks(settings):
    """Create compliance service with all mocked dependencies."""
    api_repo = Mock()
    api_repo.get = AsyncMock()
    api_repo.find_all = AsyncMock()
    
    compliance_repo = Mock()
    compliance_repo.create = AsyncMock()
    compliance_repo.update = AsyncMock()
    compliance_repo.find_by_api = AsyncMock(return_value=[])
    compliance_repo.find_by_standard = AsyncMock(return_value=[])
    compliance_repo.find_open_violations = AsyncMock(return_value=[])
    compliance_repo.get_compliance_posture = AsyncMock()
    compliance_repo.generate_audit_report_data = AsyncMock()
    
    gateway_repo = Mock()
    gateway_repo.get = AsyncMock()
    
    metrics_repo = Mock()
    metrics_repo.find_by_api = AsyncMock(return_value=([], 0))
    
    llm_service = Mock()
    llm_service.complete = AsyncMock(return_value="AI-generated executive summary")
    
    compliance_agent = ComplianceAgent(llm_service, metrics_repo)
    
    service = ComplianceService(
        settings=settings,
        api_repository=api_repo,
        compliance_repository=compliance_repo,
        llm_service=llm_service,
        compliance_agent=compliance_agent,
        metrics_repository=metrics_repo,
        gateway_repository=gateway_repo,
    )
    
    return service, api_repo, compliance_repo, llm_service


def create_test_api(
    name: str,
    base_path: str,
    auth_type: AuthenticationType = AuthenticationType.NONE,
    tags: list[str] | None = None,
) -> API:
    """Helper to create test API."""
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


class TestCompleteAuditWorkflow:
    """Test complete audit workflow from scanning to report generation."""

    @pytest.mark.asyncio
    async def test_scan_multiple_apis_and_generate_report(
        self, compliance_service_with_mocks
    ):
        """Test scanning multiple APIs and generating comprehensive audit report."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Create test APIs with different compliance issues
        apis = [
            create_test_api(
                "User API",
                "/api/v1/users",
                tags=["users", "personal-data"]
            ),
            create_test_api(
                "Payment API",
                "/api/v1/payments",
                tags=["payment", "financial"]
            ),
            create_test_api(
                "Health API",
                "/api/v1/health",
                tags=["healthcare", "medical"]
            ),
        ]
        
        # Mock API repository to return test APIs
        api_repo.find_all.return_value = apis
        
        # Step 1: Scan all APIs for compliance violations
        scan_results = []
        for api in apis:
            api_repo.get.return_value = api
            result = await service.scan_api_compliance(api.id)
            scan_results.append(result)
        
        # Verify all APIs were scanned
        assert len(scan_results) == 3
        for result in scan_results:
            assert "violations" in result
            assert len(result["violations"]) > 0
        
        # Step 2: Mock audit report data
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 3,
            "scanned_apis": 3,
            "total_violations": 15,
            "violations_by_severity": {
                "critical": 3,
                "high": 6,
                "medium": 4,
                "low": 2,
            },
            "violations_by_standard": {
                "GDPR": 5,
                "HIPAA": 3,
                "PCI_DSS": 4,
                "SOC2": 2,
                "ISO_27001": 1,
            },
            "violations_by_type": {
                "GDPR_DATA_PROTECTION_BY_DESIGN": 2,
                "HIPAA_ACCESS_CONTROL": 3,
                "PCI_DSS_NETWORK_SECURITY": 4,
            },
        }
        
        # Step 3: Generate audit report
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )
        
        # Verify report structure
        assert report is not None
        assert "report_id" in report
        assert "generated_at" in report
        assert "period" in report
        assert "summary" in report
        assert "executive_summary" in report
        
        # Verify summary data
        summary = report["summary"]
        assert summary["total_apis"] == 3
        assert summary["scanned_apis"] == 3
        assert summary["total_violations"] == 15
        assert summary["violations_by_severity"]["critical"] == 3
        
        # Verify AI-generated executive summary
        assert "AI-generated" in report["executive_summary"]

    @pytest.mark.asyncio
    async def test_audit_workflow_with_specific_standards(
        self, compliance_service_with_mocks
    ):
        """Test audit workflow for specific compliance standards."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Create healthcare API
        api = create_test_api(
            "Patient Records API",
            "/api/v1/patients",
            tags=["healthcare", "medical"]
        )
        
        api_repo.get.return_value = api
        
        # Step 1: Scan for HIPAA compliance only
        scan_result = await service.scan_api_compliance(
            api.id,
            standards=[ComplianceStandard.HIPAA]
        )
        
        assert scan_result is not None
        assert "violations" in scan_result
        
        # Verify only HIPAA violations are detected
        for violation in scan_result["violations"]:
            assert violation.standard == ComplianceStandard.HIPAA
        
        # Step 2: Mock HIPAA-specific audit data
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 1,
            "scanned_apis": 1,
            "total_violations": 5,
            "violations_by_severity": {
                "critical": 2,
                "high": 2,
                "medium": 1,
                "low": 0,
            },
            "violations_by_standard": {
                "HIPAA": 5,
            },
        }
        
        # Step 3: Generate HIPAA-specific audit report
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            standards=[ComplianceStandard.HIPAA]
        )
        
        assert report is not None
        assert report["summary"]["violations_by_standard"]["HIPAA"] == 5

    @pytest.mark.asyncio
    async def test_audit_workflow_tracks_remediation_progress(
        self, compliance_service_with_mocks
    ):
        """Test audit workflow tracks remediation progress over time."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        api = create_test_api("Test API", "/api/v1/test")
        api_repo.get.return_value = api
        
        # Step 1: Initial scan - detect violations
        initial_scan = await service.scan_api_compliance(api.id)
        assert len(initial_scan["violations"]) > 0
        
        # Step 2: Mock some violations as remediated
        remediated_violations = [
            ComplianceViolation(
                id=uuid4(),
                api_id=api.id,
                compliance_standard=ComplianceStandard.GDPR,
                violation_type=ComplianceViolationType.GDPR_DATA_PROTECTION_BY_DESIGN,
                severity=ComplianceSeverity.HIGH,
                status=ComplianceStatus.REMEDIATED,
                title="Data protection issue",
                description="Missing data protection controls",
                affected_endpoints=["/api/v1/test/data"],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow() - timedelta(days=10),
                remediation_documentation=None,
                regulatory_reference=None,
                risk_level=None,
                remediation_deadline=None,
                remediated_at=datetime.utcnow() - timedelta(days=2),
                last_audit_date=None,
                next_audit_date=None,
                metadata=None,
            )
        ]
        
        compliance_repo.find_by_api.return_value = remediated_violations
        
        # Step 3: Generate audit report showing remediation progress
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 1,
            "scanned_apis": 1,
            "total_violations": 5,
            "open_violations": 3,
            "remediated_violations": 2,
            "violations_by_severity": {
                "critical": 1,
                "high": 2,
                "medium": 1,
                "low": 1,
            },
            "remediation_rate": 40.0,  # 2 out of 5 remediated
        }
        
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )
        
        assert report is not None
        assert report["summary"]["remediated_violations"] == 2
        assert report["summary"]["remediation_rate"] == 40.0


class TestCompliancePostureTracking:
    """Test compliance posture tracking over time."""

    @pytest.mark.asyncio
    async def test_track_compliance_posture_improvement(
        self, compliance_service_with_mocks
    ):
        """Test tracking compliance posture improvement over time."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Mock initial poor compliance posture
        compliance_repo.get_compliance_posture.return_value = {
            "total_violations": 50,
            "critical_violations": 10,
            "high_violations": 20,
            "medium_violations": 15,
            "low_violations": 5,
            "compliance_score": 45.0,  # Poor score
            "by_standard": {
                "GDPR": 15,
                "HIPAA": 10,
                "PCI_DSS": 12,
                "SOC2": 8,
                "ISO_27001": 5,
            },
        }
        
        initial_posture = await service.get_compliance_posture()
        
        assert initial_posture["compliance_score"] == 45.0
        assert initial_posture["total_violations"] == 50
        
        # Simulate remediation efforts
        # Mock improved compliance posture after remediation
        compliance_repo.get_compliance_posture.return_value = {
            "total_violations": 20,
            "critical_violations": 2,
            "high_violations": 8,
            "medium_violations": 7,
            "low_violations": 3,
            "compliance_score": 75.0,  # Improved score
            "by_standard": {
                "GDPR": 6,
                "HIPAA": 4,
                "PCI_DSS": 5,
                "SOC2": 3,
                "ISO_27001": 2,
            },
        }
        
        improved_posture = await service.get_compliance_posture()
        
        assert improved_posture["compliance_score"] == 75.0
        assert improved_posture["total_violations"] == 20
        assert improved_posture["compliance_score"] > initial_posture["compliance_score"]

    @pytest.mark.asyncio
    async def test_compliance_posture_by_standard(
        self, compliance_service_with_mocks
    ):
        """Test compliance posture tracking for individual standards."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Mock GDPR-specific posture
        compliance_repo.get_compliance_posture.return_value = {
            "total_violations": 15,
            "critical_violations": 3,
            "high_violations": 6,
            "medium_violations": 4,
            "low_violations": 2,
            "compliance_score": 62.0,
        }
        
        gdpr_posture = await service.get_compliance_posture(
            standard=ComplianceStandard.GDPR
        )
        
        assert gdpr_posture["total_violations"] == 15
        assert gdpr_posture["compliance_score"] == 62.0
        
        # Mock HIPAA-specific posture
        compliance_repo.get_compliance_posture.return_value = {
            "total_violations": 10,
            "critical_violations": 2,
            "high_violations": 4,
            "medium_violations": 3,
            "low_violations": 1,
            "compliance_score": 70.0,
        }
        
        hipaa_posture = await service.get_compliance_posture(
            standard=ComplianceStandard.HIPAA
        )
        
        assert hipaa_posture["total_violations"] == 10
        assert hipaa_posture["compliance_score"] == 70.0


class TestAuditReportFormats:
    """Test different audit report formats and options."""

    @pytest.mark.asyncio
    async def test_generate_detailed_audit_report(
        self, compliance_service_with_mocks
    ):
        """Test generating detailed audit report with all sections."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Mock comprehensive audit data
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 100,
            "scanned_apis": 98,
            "total_violations": 75,
            "violations_by_severity": {
                "critical": 10,
                "high": 25,
                "medium": 30,
                "low": 10,
            },
            "violations_by_standard": {
                "GDPR": 20,
                "HIPAA": 15,
                "PCI_DSS": 18,
                "SOC2": 12,
                "ISO_27001": 10,
            },
            "violations_by_type": {
                "GDPR_DATA_PROTECTION_BY_DESIGN": 8,
                "HIPAA_ACCESS_CONTROL": 7,
                "PCI_DSS_NETWORK_SECURITY": 9,
                "SOC2_SECURITY_AVAILABILITY": 6,
                "ISO_27001_ACCESS_CONTROL": 5,
            },
            "top_violating_apis": [
                {"api_id": str(uuid4()), "api_name": "Payment API", "violation_count": 12},
                {"api_id": str(uuid4()), "api_name": "User API", "violation_count": 10},
                {"api_id": str(uuid4()), "api_name": "Health API", "violation_count": 8},
            ],
        }
        
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=90),
            end_date=datetime.utcnow(),
        )
        
        assert report is not None
        assert "report_id" in report
        assert "generated_at" in report
        assert "period" in report
        assert "summary" in report
        assert "executive_summary" in report
        
        # Verify all sections are present
        summary = report["summary"]
        assert "total_apis" in summary
        assert "violations_by_severity" in summary
        assert "violations_by_standard" in summary
        assert "violations_by_type" in summary
        assert "top_violating_apis" in summary

    @pytest.mark.asyncio
    async def test_generate_summary_audit_report(
        self, compliance_service_with_mocks
    ):
        """Test generating summary audit report for executive review."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Mock summary audit data
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 100,
            "scanned_apis": 98,
            "total_violations": 75,
            "compliance_score": 68.5,
            "violations_by_severity": {
                "critical": 10,
                "high": 25,
                "medium": 30,
                "low": 10,
            },
        }
        
        # Mock AI-generated executive summary
        llm_service.complete.return_value = (
            "Executive Summary: The organization demonstrates moderate compliance posture "
            "with a score of 68.5%. Critical attention required for 10 critical violations "
            "across payment and healthcare APIs. Recommend immediate remediation of "
            "authentication and encryption issues."
        )
        
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )
        
        assert report is not None
        assert "executive_summary" in report
        assert "moderate compliance posture" in report["executive_summary"].lower()
        assert "68.5%" in report["executive_summary"]


class TestMultiStandardAuditReporting:
    """Test audit reporting across multiple compliance standards."""

    @pytest.mark.asyncio
    async def test_generate_multi_standard_audit_report(
        self, compliance_service_with_mocks
    ):
        """Test generating audit report covering multiple standards."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        # Mock multi-standard audit data
        compliance_repo.generate_audit_report_data.return_value = {
            "total_apis": 50,
            "scanned_apis": 48,
            "total_violations": 40,
            "violations_by_standard": {
                "GDPR": 12,
                "HIPAA": 10,
                "PCI_DSS": 18,
            },
            "compliance_scores_by_standard": {
                "GDPR": 72.0,
                "HIPAA": 75.0,
                "PCI_DSS": 65.0,
            },
        }
        
        report = await service.generate_audit_report(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            standards=[
                ComplianceStandard.GDPR,
                ComplianceStandard.HIPAA,
                ComplianceStandard.PCI_DSS,
            ]
        )
        
        assert report is not None
        assert report["summary"]["violations_by_standard"]["GDPR"] == 12
        assert report["summary"]["violations_by_standard"]["HIPAA"] == 10
        assert report["summary"]["violations_by_standard"]["PCI_DSS"] == 18

    @pytest.mark.asyncio
    async def test_compare_compliance_across_standards(
        self, compliance_service_with_mocks
    ):
        """Test comparing compliance posture across different standards."""
        service, api_repo, compliance_repo, llm_service = compliance_service_with_mocks
        
        standards = [
            ComplianceStandard.GDPR,
            ComplianceStandard.HIPAA,
            ComplianceStandard.SOC2,
        ]
        
        postures = {}
        for standard in standards:
            # Mock different postures for each standard
            if standard == ComplianceStandard.GDPR:
                compliance_repo.get_compliance_posture.return_value = {
                    "total_violations": 12,
                    "compliance_score": 72.0,
                }
            elif standard == ComplianceStandard.HIPAA:
                compliance_repo.get_compliance_posture.return_value = {
                    "total_violations": 8,
                    "compliance_score": 80.0,
                }
            else:  # SOC2
                compliance_repo.get_compliance_posture.return_value = {
                    "total_violations": 15,
                    "compliance_score": 65.0,
                }
            
            postures[standard] = await service.get_compliance_posture(standard=standard)
        
        # Verify different compliance scores
        assert postures[ComplianceStandard.GDPR]["compliance_score"] == 72.0
        assert postures[ComplianceStandard.HIPAA]["compliance_score"] == 80.0
        assert postures[ComplianceStandard.SOC2]["compliance_score"] == 65.0
        
        # HIPAA has best compliance
        assert postures[ComplianceStandard.HIPAA]["compliance_score"] > postures[ComplianceStandard.GDPR]["compliance_score"]
        assert postures[ComplianceStandard.HIPAA]["compliance_score"] > postures[ComplianceStandard.SOC2]["compliance_score"]


# Made with Bob