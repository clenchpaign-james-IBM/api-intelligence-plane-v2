"""Integration tests for security scanning functionality.

Tests the complete security scanning workflow including:
- Hybrid scanning (rule-based + AI)
- Multi-source data analysis
- Compliance detection
- Vulnerability detection
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.security_service import SecurityService
from backend.app.agents.security_agent import SecurityAgent
from backend.app.models.api import API, AuthenticationType, Endpoint
from backend.app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    ComplianceStandard,
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
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_api = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_metrics_repository():
    """Create mock metrics repository."""
    repo = Mock()
    repo.get_latest_metrics = AsyncMock(return_value={
        "request_count": 1000,
        "error_rate": 0.05,
        "response_time_p95": 250.0,
    })
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
    service.complete = AsyncMock(return_value="AI analysis result")
    return service


@pytest.fixture
def mock_security_agent(mock_llm_service, mock_metrics_repository):
    """Create mock security agent."""
    agent = SecurityAgent(mock_llm_service, mock_metrics_repository)
    return agent


@pytest.fixture
def security_service(
    settings,
    mock_api_repository,
    mock_vulnerability_repository,
    mock_llm_service,
    mock_security_agent,
    mock_metrics_repository,
    mock_gateway_repository,
):
    """Create security service instance."""
    return SecurityService(
        settings=settings,
        api_repository=mock_api_repository,
        vulnerability_repository=mock_vulnerability_repository,
        llm_service=mock_llm_service,
        security_agent=mock_security_agent,
        metrics_repository=mock_metrics_repository,
        gateway_repository=mock_gateway_repository,
    )


@pytest.fixture
def sample_api():
    """Create a sample API for testing."""
    return API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="Payment API",
        version="v1",
        base_path="/api/v1/payments",
        endpoints=[
            Endpoint(
                path="/api/v1/payments/process",
                method="POST",
                description="Process payment",
            ),
            Endpoint(
                path="/api/v1/payments/{id}",
                method="GET",
                description="Get payment details",
            ),
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.NONE,
        tags=["payment", "financial"],
        is_shadow=False,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
    )


class TestHybridScanning:
    """Test hybrid security scanning (rule-based + AI)."""

    @pytest.mark.asyncio
    async def test_scan_api_without_authentication(
        self, security_service, sample_api, mock_api_repository
    ):
        """Test scanning API without authentication."""
        mock_api_repository.get.return_value = sample_api

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        assert "vulnerabilities" in result
        assert len(result["vulnerabilities"]) > 0
        
        # Should detect missing authentication
        auth_vulns = [
            v for v in result["vulnerabilities"]
            if v.vulnerability_type == VulnerabilityType.AUTHENTICATION
        ]
        assert len(auth_vulns) > 0

    @pytest.mark.asyncio
    async def test_scan_api_with_high_traffic(
        self, security_service, sample_api, mock_api_repository, mock_metrics_repository
    ):
        """Test scanning API with high traffic (should detect rate limiting issues)."""
        mock_api_repository.get.return_value = sample_api
        
        # Mock high traffic metrics
        mock_metrics_repository.get_latest_metrics.return_value = {
            "request_count": 10000,
            "requests_per_minute": 2000,
            "burst_detected": True,
            "error_rate": 0.15,
        }

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        assert "vulnerabilities" in result
        
        # Should detect rate limiting issues
        rate_limit_vulns = [
            v for v in result["vulnerabilities"]
            if "rate limit" in v.title.lower()
        ]
        assert len(rate_limit_vulns) > 0


class TestComplianceDetection:
    """Test compliance detection (GDPR, HIPAA, PCI-DSS, SOC2)."""

    @pytest.mark.asyncio
    async def test_detect_gdpr_compliance_issues(
        self, security_service, mock_api_repository
    ):
        """Test GDPR compliance detection for personal data APIs."""
        # Create API with personal data endpoints
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name="User Profile API",
            version="v1",
            base_path="/api/v1/users",
            endpoints=[
                Endpoint(
                    path="/api/v1/users/profile",
                    method="GET",
                    description="Get user profile with personal data",
                ),
            ],
            methods=["GET"],
            authentication_type=AuthenticationType.NONE,
            tags=["users", "personal-data"],
            is_shadow=False,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
        )
        
        mock_api_repository.get.return_value = api

        result = await security_service.scan_api_security(api.id)

        assert result is not None
        
        # Should detect GDPR compliance issues
        compliance_issues = result.get("compliance_issues", [])
        assert ComplianceStandard.GDPR in compliance_issues

    @pytest.mark.asyncio
    async def test_detect_hipaa_compliance_issues(
        self, security_service, mock_api_repository
    ):
        """Test HIPAA compliance detection for healthcare APIs."""
        # Create API with healthcare endpoints
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name="Patient Records API",
            version="v1",
            base_path="/api/v1/health",
            endpoints=[
                Endpoint(
                    path="/api/v1/health/patient/{id}",
                    method="GET",
                    description="Get patient medical records",
                ),
            ],
            methods=["GET"],
            authentication_type=AuthenticationType.NONE,
            tags=["healthcare", "medical"],
            is_shadow=False,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
        )
        
        mock_api_repository.get.return_value = api

        result = await security_service.scan_api_security(api.id)

        assert result is not None
        
        # Should detect HIPAA compliance issues
        compliance_issues = result.get("compliance_issues", [])
        assert ComplianceStandard.HIPAA in compliance_issues

    @pytest.mark.asyncio
    async def test_detect_pci_dss_compliance_issues(
        self, security_service, sample_api, mock_api_repository
    ):
        """Test PCI-DSS compliance detection for payment APIs."""
        mock_api_repository.get.return_value = sample_api

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        
        # Should detect PCI-DSS compliance issues (payment API without proper security)
        compliance_issues = result.get("compliance_issues", [])
        assert ComplianceStandard.PCI_DSS in compliance_issues


class TestMultiSourceDataAnalysis:
    """Test multi-source data analysis (metadata + metrics + traffic)."""

    @pytest.mark.asyncio
    async def test_analyze_with_traffic_patterns(
        self, security_service, sample_api, mock_api_repository, mock_metrics_repository
    ):
        """Test security analysis using traffic patterns."""
        mock_api_repository.get.return_value = sample_api
        
        # Mock traffic analysis data
        mock_metrics_repository.get_latest_metrics.return_value = {
            "request_count": 5000,
            "unauthorized_attempts": 150,
            "malformed_requests": 50,
            "injection_attempts": 10,
            "cross_origin_requests": 200,
            "cors_blocked_requests": 50,
        }

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        assert "vulnerabilities" in result
        
        # Should detect multiple issues based on traffic
        vulns = result["vulnerabilities"]
        assert len(vulns) > 0
        
        # Check for authorization issues
        authz_vulns = [
            v for v in vulns
            if v.vulnerability_type == VulnerabilityType.AUTHORIZATION
        ]
        assert len(authz_vulns) > 0

    @pytest.mark.asyncio
    async def test_analyze_with_api_metadata(
        self, security_service, mock_api_repository
    ):
        """Test security analysis using API metadata."""
        # Create API with specific metadata
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name="Admin API",
            version="v1",
            base_path="/api/v1/admin",
            endpoints=[
                Endpoint(
                    path="/api/v1/admin/users/delete",
                    method="DELETE",
                    description="Delete user account",
                ),
            ],
            methods=["DELETE"],
            authentication_type=AuthenticationType.NONE,  # No auth on admin endpoint!
            tags=["admin", "privileged"],
            is_shadow=False,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
        )
        
        mock_api_repository.get.return_value = api

        result = await security_service.scan_api_security(api.id)

        assert result is not None
        assert "vulnerabilities" in result
        
        # Should detect critical authentication issue on admin endpoint
        auth_vulns = [
            v for v in result["vulnerabilities"]
            if v.vulnerability_type == VulnerabilityType.AUTHENTICATION
            and v.severity == VulnerabilitySeverity.CRITICAL
        ]
        assert len(auth_vulns) > 0


class TestVulnerabilityDetection:
    """Test specific vulnerability detection."""

    @pytest.mark.asyncio
    async def test_detect_missing_cors_policy(
        self, security_service, sample_api, mock_api_repository, mock_metrics_repository
    ):
        """Test CORS policy detection."""
        mock_api_repository.get.return_value = sample_api
        
        # Mock CORS-related traffic
        mock_metrics_repository.get_latest_metrics.return_value = {
            "cross_origin_requests": 500,
            "cors_blocked_requests": 100,
            "unique_origins": 50,
        }

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        
        # Should detect CORS issues
        cors_vulns = [
            v for v in result["vulnerabilities"]
            if "cors" in v.title.lower()
        ]
        assert len(cors_vulns) > 0

    @pytest.mark.asyncio
    async def test_detect_missing_validation(
        self, security_service, sample_api, mock_api_repository, mock_metrics_repository
    ):
        """Test input validation detection."""
        mock_api_repository.get.return_value = sample_api
        
        # Mock validation-related traffic
        mock_metrics_repository.get_latest_metrics.return_value = {
            "malformed_requests": 100,
            "injection_attempts": 25,
        }

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        
        # Should detect validation issues
        validation_vulns = [
            v for v in result["vulnerabilities"]
            if "validation" in v.title.lower()
        ]
        assert len(validation_vulns) > 0

    @pytest.mark.asyncio
    async def test_detect_missing_security_headers(
        self, security_service, sample_api, mock_api_repository, mock_metrics_repository
    ):
        """Test security headers detection."""
        mock_api_repository.get.return_value = sample_api
        
        # Mock security attack attempts
        mock_metrics_repository.get_latest_metrics.return_value = {
            "xss_attempts": 15,
            "clickjacking_attempts": 10,
            "mime_sniffing_issues": 5,
        }

        result = await security_service.scan_api_security(sample_api.id)

        assert result is not None
        
        # Should detect security headers issues
        headers_vulns = [
            v for v in result["vulnerabilities"]
            if "security header" in v.title.lower()
        ]
        assert len(headers_vulns) > 0


class TestScanAllAPIs:
    """Test scanning all APIs."""

    @pytest.mark.asyncio
    async def test_scan_all_apis(
        self, security_service, sample_api, mock_api_repository
    ):
        """Test scanning multiple APIs."""
        # Create multiple APIs
        apis = [sample_api]
        for i in range(3):
            api = API(
                id=uuid4(),
                gateway_id=sample_api.gateway_id,
                name=f"Test API {i}",
                version="v1",
                base_path=f"/api/v1/test{i}",
                endpoints=[
                    Endpoint(
                        path=f"/api/v1/test{i}/resource",
                        method="GET",
                    ),
                ],
                methods=["GET"],
                authentication_type=AuthenticationType.NONE,
                is_shadow=False,
                discovered_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
            )
            apis.append(api)
        
        mock_api_repository.get_all.return_value = apis

        result = await security_service.scan_all_apis()

        assert result is not None
        assert "total_apis" in result
        assert result["total_apis"] == len(apis)
        assert "vulnerabilities_found" in result
        assert result["vulnerabilities_found"] > 0


# Made with Bob